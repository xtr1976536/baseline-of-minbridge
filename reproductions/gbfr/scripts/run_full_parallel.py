"""Operational sharding of the frozen GBFR run; no model or label changes."""
import asyncio
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/gpt56_sol_full'
SNAPSHOT=OUT/'source_snapshot'
sys.path.insert(0,str(SNAPSHOT))
from gbfr.data import sha256,write_json
from gbfr.llm import APIError,ChatClient
from gbfr.runner import preflight,resolve_paths,recover_journal,run_cell,report
from gbfr.types import dumps

BACKBONE='GPT-5.6 Sol'
SHARD_SIZE=128
PARALLEL_SHARDS=8


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--datasets',nargs='+',choices=['CFBenchmark','FinanceReasoning','FinQA','TAT-QA'])
    parser.add_argument('--retry-service-errors',action='store_true')
    parser.add_argument('--prepare-service-retry-only',action='store_true')
    parser.add_argument('--check-scope',action='store_true')
    args=parser.parse_args()
    pause_path=OUT/'scheduling/user_pause.json'
    if not args.check_scope and pause_path.exists() and json.loads(pause_path.read_text(encoding='utf-8-sig')).get('paused'):
        raise SystemExit('Full experiment remains paused by the user. Only the separate small-validation runner is authorized.')
    config=resolve_paths(SNAPSHOT/'configs/run.json')
    graph,datasets=preflight(config)
    scope_path=ROOT/'configs/gpt56_sol_scope.json'
    scope=json.loads(scope_path.read_text(encoding='utf-8')) if scope_path.exists() else {}
    selected=args.datasets or scope.get('datasets') or list(datasets)
    if not selected or len(set(selected))!=len(selected) or set(selected)-set(datasets):
        raise RuntimeError('Invalid selected datasets')
    active={'datasets':selected,'counts':{name:len(datasets[name]) for name in selected},
            'total':sum(len(datasets[name]) for name in selected),'selection_source':str(scope_path) if not args.datasets and scope else 'command line'}
    if not args.datasets and scope.get('expected_counts') and active['counts']!=scope['expected_counts']:
        raise RuntimeError('Selected counts changed')
    if args.check_scope:
        print(dumps(active));return
    write_json(OUT/'scheduling/active_scope.json',active)
    frozen=json.loads((OUT/'full_run_manifest.json').read_text(encoding='utf-8'))
    for name,digest in frozen['source_sha256'].items():
        if sha256(SNAPSHOT/name)!=digest:raise RuntimeError('Frozen source changed: '+name)
    if '--retry-service-errors' in sys.argv:
        state=json.loads((OUT/'process_state.json').read_text(encoding='utf-8'))
        if not state.get('finished_at'):raise RuntimeError('Previous process has not exited')
        archive=OUT/'scheduling'/('service_retry_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        changes=[]
        for path in (OUT/'shards').rglob('predictions.jsonl'):
            if path.relative_to(OUT/'shards').parts[0] not in selected:continue
            old=recover_journal(path)
            retry=[p for p in old if p.get('error_type')=='APIError' and
                   (re.search(r'HTTP (?:401|402|403|429|5\d\d)',p.get('error','')) or p.get('error','').startswith('Transport failure'))]
            if not retry:continue
            saved=archive/path.relative_to(OUT/'shards')
            saved.parent.mkdir(parents=True,exist_ok=True)
            saved.write_bytes(path.read_bytes())
            ids={p['sample_id'] for p in retry}
            path.write_text(''.join(dumps(p)+'\n' for p in old if p['sample_id'] not in ids),encoding='utf-8')
            changes.append({'journal':str(path),'archive':str(saved),'retry_ids':sorted(ids)})
        write_json(archive/'retry_manifest.json',{'reason':'Retry only service-rejected requests; preserve all valid model outputs and model protocol/program errors. No gold consulted.','changes':changes})
        print('SERVICE_REQUEUED '+str(sum(len(c['retry_ids']) for c in changes)),flush=True)
        if '--prepare-service-retry-only' in sys.argv:return
    state_path=OUT/'process_state.json'
    if state_path.exists():
        prior=OUT/'scheduling'/f'process_state_prior_to_{os.getpid()}.json'
        if not prior.exists():prior.write_bytes(state_path.read_bytes())
    write_json(state_path,{'pid':os.getpid(),'started_at':datetime.now(timezone.utc).isoformat(),
        'status':'running','exit_code':None,'datasets':selected,'total':active['total'],
        'controller':'independent Python process; state written by the run itself'})
    # Shared exact-request locks make the existing single-request cache safe
    # across these clients. Each still has the frozen two-request semaphore.
    shared_locks={}
    original_init=ChatClient.__init__
    service_log=OUT/'scheduling/service_errors.jsonl'
    def shared_cache_init(self,*args,**kwargs):
        original_init(self,*args,**kwargs)
        self.locks=shared_locks
        self.last_service_detail=''
        async def capture(response):
            if response.status_code<400:return
            await response.aread()
            try:body=response.json();detail=body.get('error',body)
            except ValueError:detail={'message':response.text[:1500]}
            if isinstance(detail,dict):detail={k:detail[k] for k in ('code','type','message','detail') if k in detail}
            safe=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',json.dumps(detail,ensure_ascii=False).replace(self.api_key,'[REDACTED]'))
            self.last_service_detail=safe
            with service_log.open('a',encoding='utf-8') as stream:
                stream.write(dumps({'at':datetime.now(timezone.utc).isoformat(),'status_code':response.status_code,'error':json.loads(safe)})+'\n')
        self.http.event_hooks['response']=[capture]
    ChatClient.__init__=shared_cache_init
    original_complete=ChatClient._complete
    async def retry_service_only(self,*args,**kwargs):
        for attempt in range(4):
            try:return await original_complete(self,*args,**kwargs)
            except APIError as exc:
                status=getattr(exc,'status_code',None)
                transient=status in {403,429} or (status is not None and status>=500) or str(exc).startswith('Transport failure')
                hard=any(word in self.last_service_detail.casefold() for word in ('billing_error','insufficient balance','insufficient_balance','insufficient_quota','余额不足','无可用额度'))
                if not transient or hard or attempt==3:raise
                await asyncio.sleep(5*(2**attempt))
                self.fatal_error=None
    ChatClient._complete=retry_service_only
    shards=[]
    for name,rows in datasets.items():
        original=OUT/BACKBONE/name/'predictions.jsonl'
        seed_path=OUT/'scheduling'/name/'initial_predictions.jsonl'
        seed_path.parent.mkdir(parents=True,exist_ok=True)
        if not seed_path.exists():
            seed_path.write_bytes(original.read_bytes() if original.exists() else b'')
        previous={p['sample_id']:p for p in recover_journal(seed_path)}
        for index,start in enumerate(range(0,len(rows),SHARD_SIZE)):
            chunk=rows[start:start+SHARD_SIZE]
            shard_root=OUT/'shards'/name/f'{index:03d}'
            journal=shard_root/BACKBONE/name/'predictions.jsonl'
            journal.parent.mkdir(parents=True,exist_ok=True)
            if not journal.exists():
                journal.write_text(''.join(dumps(previous[s['id']])+'\n' for s in chunk if s['id'] in previous),encoding='utf-8')
            shard_config=deepcopy(config)
            shard_config['output_dir']=str(shard_root)
            shards.append({'dataset':name,'index':index,'n':len(chunk),
                'sample_ids':[s['id'] for s in chunk],'journal':str(journal),
                'config':shard_config,'samples':chunk})
    ledger={'created_at':datetime.now(timezone.utc).isoformat(),
        'orchestrator_sha256':sha256(Path(__file__)),
        'reason':'Operational throughput only; preserve every completed prediction, including errors. Frozen source, model request bodies, graph, datasets and evaluation are unchanged.',
        'parallel_shards':PARALLEL_SHARDS,'api_concurrency_per_client':2,
        'maximum_total_api_concurrency':PARALLEL_SHARDS*2,
        'shared_exact_request_cache':True,
        'shards':[{k:s[k] for k in ('dataset','index','n','sample_ids','journal')} for s in shards]}
    ledger_path=OUT/'scheduling/parallel_manifest.json'
    if ledger_path.exists():
        old=json.loads(ledger_path.read_text(encoding='utf-8'))
        if old['shards']!=ledger['shards']:raise RuntimeError('Shard identity changed')
    else:write_json(ledger_path,ledger)
    source_archive=OUT/'scheduling'/('orchestrator_'+sha256(Path(__file__))+'.py')
    if not source_archive.exists():source_archive.write_bytes(Path(__file__).read_bytes())
    with (OUT/'scheduling/epochs.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(dumps({'started_at':datetime.now(timezone.utc).isoformat(),'orchestrator_sha256':sha256(Path(__file__)),
            'parallel_shards':PARALLEL_SHARDS,'maximum_api_concurrency':PARALLEL_SHARDS*2,
            'datasets':selected,'total_examples':active['total'],
            'dispatch_order':'round_robin_by_shard_index',
            'service_retry_attempts':4,'service_retry_wait_seconds':[5,10,20],
            'successful_responses_and_protocol_errors_retried':False})+'\n')
    stop=asyncio.Event()
    sem=asyncio.Semaphore(PARALLEL_SHARDS)
    failures=[]
    tasks=[]
    async def work(s):
        async with sem:
            if stop.is_set():return
            try:
                await run_cell(s['config'],graph,s['dataset'],s['samples'],BACKBONE)
                print('SHARD_DONE '+s['dataset']+'/'+str(s['index']),flush=True)
            except Exception as exc:
                failures.append({'dataset':s['dataset'],'shard':s['index'],'type':type(exc).__name__,'message':str(exc)})
                stop.set()
                print('SHARD_INTERRUPTED '+dumps(failures[-1]),flush=True)
                for task in tasks:
                    if task is not asyncio.current_task() and not task.done():task.cancel()
    try:
        dispatch=sorted((s for s in shards if s['dataset'] in selected),key=lambda s:(s['index'],selected.index(s['dataset'])))
        tasks=[asyncio.create_task(work(s)) for s in dispatch]
        await asyncio.gather(*tasks,return_exceptions=True)
    finally:
        for name,rows in datasets.items():
            if name not in selected:continue
            merged={}
            usages=[]
            for s in shards:
                if s['dataset']!=name:continue
                for p in recover_journal(Path(s['journal'])):
                    if p['sample_id'] in merged:raise RuntimeError('Duplicate shard prediction')
                    merged[p['sample_id']]=p
                usage=Path(s['journal']).parent/'api_usage.json'
                if usage.exists():usages.extend(json.loads(usage.read_text(encoding='utf-8')))
            target=OUT/BACKBONE/name/'predictions.jsonl'
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_suffix('.merge.tmp')
            temporary.write_text(''.join(dumps(merged[s['id']])+'\n' for s in rows if s['id'] in merged),encoding='utf-8')
            temporary.replace(target)
            write_json(target.parent/'api_usage.json',usages)
            if len(merged)==len(rows):
                await run_cell(config,graph,name,rows,BACKBONE)
            else:
                from gbfr.metrics import summarize
                write_json(target.parent/'metrics.json',summarize(rows,list(merged.values()),config['evaluation']['unspecified_decimals']))
        if len(selected)==len(datasets):report(config)
        else:
            import runpy
            runpy.run_path(str(ROOT/'scripts/summarize_full_run.py'),run_name='__main__',init_globals={'SELECTED_DATASETS':selected})
        write_json(OUT/'scheduling/outcome.json',{'finished_at':datetime.now(timezone.utc).isoformat(),'datasets':selected,'total_examples':active['total'],'failures':failures})
    if failures:raise RuntimeError('Full run interrupted: '+dumps(failures))


def finish_process_state(exit_code,failure=None):
    path=OUT/'process_state.json'
    if not path.exists():return
    state=json.loads(path.read_text(encoding='utf-8'))
    if state.get('pid')!=os.getpid():return
    state.update(finished_at=datetime.now(timezone.utc).isoformat(),exit_code=exit_code,status='finished')
    if failure:state['failure_type']=failure
    write_json(path,state)

if __name__=='__main__':
    try:asyncio.run(main())
    except BaseException as exc:
        finish_process_state(1,type(exc).__name__)
        raise
    else:finish_process_state(0)
