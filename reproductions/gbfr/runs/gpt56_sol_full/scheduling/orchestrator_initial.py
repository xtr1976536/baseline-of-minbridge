"""Operational sharding of the frozen GBFR run; no model or label changes."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/gpt56_sol_full'
SNAPSHOT=OUT/'source_snapshot'
sys.path.insert(0,str(SNAPSHOT))
from gbfr.data import sha256,write_json
from gbfr.llm import ChatClient
from gbfr.runner import preflight,resolve_paths,recover_journal,run_cell,report
from gbfr.types import dumps

BACKBONE='GPT-5.6 Sol'
SHARD_SIZE=128
PARALLEL_SHARDS=8


async def main():
    config=resolve_paths(SNAPSHOT/'configs/run.json')
    graph,datasets=preflight(config)
    frozen=json.loads((OUT/'full_run_manifest.json').read_text(encoding='utf-8'))
    for name,digest in frozen['source_sha256'].items():
        if sha256(SNAPSHOT/name)!=digest:raise RuntimeError('Frozen source changed: '+name)
    # Shared exact-request locks make the existing single-request cache safe
    # across these clients. Each still has the frozen two-request semaphore.
    shared_locks={}
    original_init=ChatClient.__init__
    def shared_cache_init(self,*args,**kwargs):
        original_init(self,*args,**kwargs)
        self.locks=shared_locks
    ChatClient.__init__=shared_cache_init
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
    stop=asyncio.Event()
    sem=asyncio.Semaphore(PARALLEL_SHARDS)
    failures=[]
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
    try:
        await asyncio.gather(*(work(s) for s in shards))
    finally:
        for name,rows in datasets.items():
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
        report(config)
        write_json(OUT/'scheduling/outcome.json',{'finished_at':datetime.now(timezone.utc).isoformat(),'failures':failures})
    if failures:raise RuntimeError('Full run interrupted: '+dumps(failures))


if __name__=='__main__':asyncio.run(main())
