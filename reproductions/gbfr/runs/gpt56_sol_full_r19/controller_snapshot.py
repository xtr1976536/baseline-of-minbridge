"""Run the explicitly authorized R19 FinQA/TAT-QA experiment in isolation.

No older prediction is seeded into this run. Exact request caches are reusable.
Progress reads journals incrementally; it never sends model requests.
"""
import argparse
import asyncio
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'pyproject.toml').is_file() and (p/'data/main').is_dir())
OUT=ROOT/'runs/gpt56_sol_full_r19'
VALIDATED=ROOT/'runs/gbfr_refusal_validation/r19'
BACKBONE='GPT-5.6 Sol'
COUNTS={'FinQA':1096,'TAT-QA':1229}
SHARD_SIZE=128
PARALLEL_SHARDS=4

def now():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tmp.replace(p)

def pid_alive(pid):
    if os.name!='nt':
        try:os.kill(int(pid),0);return True
        except ProcessLookupError:return False
        except PermissionError:return True
    import ctypes
    from ctypes import wintypes
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.GetExitCodeProcess.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
    h=k.OpenProcess(0x1000,False,int(pid))
    if not h:return False if ctypes.get_last_error()==87 else True
    try:
        code=wintypes.DWORD()
        if not k.GetExitCodeProcess(h,ctypes.byref(code)):return True
        return code.value==259
    finally:k.CloseHandle(h)

def runtime():
    sys.path.insert(0,str(OUT/'source_snapshot'))
    from gbfr.runner import preflight,run_cell,recover_journal,run_identity
    from gbfr.llm import ChatClient
    from gbfr.metrics import summarize
    return preflight,run_cell,recover_journal,run_identity,ChatClient,summarize

def verify_frozen():
    m=load(OUT/'full_run_manifest.json')
    if m['counts']!=COUNTS:raise RuntimeError('Full scope changed')
    for name,digest in m['source_sha256'].items():
        if sha(OUT/'source_snapshot/gbfr'/name)!=digest:raise RuntimeError('Frozen source changed: '+name)
    if sha(OUT/'source_snapshot/configs/run.json')!=m['configuration_sha256']:raise RuntimeError('Frozen configuration changed')
    cfg=load(OUT/'source_snapshot/configs/run.json')
    if sha(Path(cfg['asset_lock']))!=m['asset_lock_sha256']:raise RuntimeError('Asset lock changed')
    for name,digest in m['datasets_sha256'].items():
        if sha(Path(cfg['data_dir'])/(name+'.jsonl'))!=digest:raise RuntimeError('Dataset changed: '+name)
    if sha(Path(__file__))!=m['controller_sha256']:raise RuntimeError('Use the frozen controller_snapshot.py for this run')
    return cfg,m

def prepare():
    if (OUT/'full_run_manifest.json').exists():return verify_frozen()
    expected=load(VALIDATED/'version.json')['identity']['source_sha256']
    actual={p.relative_to(ROOT/'gbfr').as_posix():sha(p) for p in (ROOT/'gbfr').rglob('*') if p.suffix in {'.py','.txt'} and '__pycache__' not in p.parts}
    if actual!=expected:raise RuntimeError('Current GBFR differs from the validated R19 source')
    scope=load(ROOT/'configs/gpt56_sol_scope.json')
    if scope['datasets']!=list(COUNTS) or scope['expected_counts']!=COUNTS:raise RuntimeError('Authorized dataset scope changed')
    for suite in ['regression','holdout']:
        if not all(m['complete'] for m in load(VALIDATED/suite/'results.json')['datasets'].values()):raise RuntimeError('R19 validation is incomplete')
    OUT.mkdir(parents=True,exist_ok=True)
    snapshot=OUT/'source_snapshot/gbfr'
    if not snapshot.exists():shutil.copytree(VALIDATED/'source_snapshot/gbfr',snapshot,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name,digest in expected.items():
        if sha(snapshot/name)!=digest:raise RuntimeError('Source copy mismatch')
    cfg=deepcopy(load(VALIDATED/'regression/configuration.json'))
    cfg['output_dir']=str(OUT)
    cfg['user_instruction']='User explicitly authorized starting the full R19 FinQA/TAT-QA run after reviewing small-sample results. Earlier full-run pause is superseded only for this new run.'
    cfg['validation_manifest_sha256']=hashlib.sha256(json.dumps({'full_scope':COUNTS,'source':'r19'},sort_keys=True).encode()).hexdigest()
    cfg['selected_datasets']=list(COUNTS)
    cfg['backbones'][BACKBONE].pop('cache_only',None)
    write(OUT/'source_snapshot/configs/run.json',cfg)
    write(OUT/'configuration.json',cfg)
    preflight,*_=runtime();_,datasets=preflight(cfg)
    if {n:len(datasets[n]) for n in COUNTS}!=COUNTS:raise RuntimeError('Full denominator mismatch')
    (OUT/'controller_snapshot.py').write_bytes(Path(__file__).read_bytes())
    manifest={'created_at':now(),'source_version':'r19','source_sha256':expected,
        'counts':COUNTS,'total':sum(COUNTS.values()),'backbone':BACKBONE,'model':'gpt-5.6-sol',
        'configuration_sha256':sha(OUT/'source_snapshot/configs/run.json'),'asset_lock_sha256':sha(Path(cfg['asset_lock'])),
        'datasets_sha256':{n:sha(Path(cfg['data_dir'])/(n+'.jsonl')) for n in COUNTS},
        'controller_sha256':sha(Path(__file__)),'parallel_shards':PARALLEL_SHARDS,
        'maximum_api_concurrency':PARALLEL_SHARDS*cfg['backbones'][BACKBONE]['concurrency'],
        'seeded_old_predictions':False,'exact_request_cache_reused':True,'full_run_authorized':True,
        'authorization':'User: 开始全量运行. Existing FinQA/TAT-QA scope retained.',
        'source_validation':'runs/gbfr_refusal_validation/r19; all metric thresholds were not met; user nevertheless explicitly authorized full execution.',
        'historical_run_preserved':'runs/gpt56_sol_full'}
    write(OUT/'full_run_manifest.json',manifest)
    write(OUT/'control.json',{'paused':False,'authorized_at':now(),'requested_by':'user','datasets':list(COUNTS),'full_run_authorized':True})
    write(OUT/'process_state.json',{'status':'prepared','total':sum(COUNTS.values()),'source_version':'r19'})
    return cfg,manifest

def acquire_lock():
    path=OUT/'run.lock'
    if path.exists():
        prior=load(path)
        if pid_alive(prior['pid']):raise RuntimeError('This experiment already has a live worker')
        archive=OUT/'lock_history'/('stale_'+str(prior['pid'])+'_'+str(os.getpid())+'.json')
        archive.parent.mkdir(exist_ok=True);archive.write_bytes(path.read_bytes());path.unlink()
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'started_at':now()},f)

def compact(p):return {k:p[k] for k in ('sample_id','status','value','meta','precision','error_type') if k in p}

class JournalIndex:
    def __init__(self):self.offsets={};self.rows={n:{} for n in COUNTS}
    def poll(self,shards):
        for s in shards:
            path=s['journal']
            if not path.exists():continue
            with path.open('rb') as f:
                f.seek(self.offsets.get(path,0))
                while True:
                    line=f.readline()
                    if not line or not line.endswith(b'\n'):break
                    p=json.loads(line);ident=p['sample_id']
                    if ident not in s['ids'] or ident in self.rows[s['dataset']]:raise RuntimeError('Unrelated or duplicate journal prediction')
                    self.rows[s['dataset']][ident]=compact(p)
                    self.offsets[path]=f.tell()

def merge_journals(shards,name,samples,target):
    locations={}
    for s in shards:
        if s['dataset']!=name or not s['journal'].exists():continue
        with s['journal'].open('rb') as f:
            while True:
                offset=f.tell();line=f.readline()
                if not line:break
                if not line.endswith(b'\n'):raise RuntimeError('Unfinished journal during merge')
                ident=json.loads(line)['sample_id']
                if ident not in s['ids'] or ident in locations:raise RuntimeError('Unrelated or duplicate merge record')
                locations[ident]=(s['journal'],offset,len(line))
    target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix('.merge.tmp')
    with ExitStack() as stack:
        handles={p:stack.enter_context(p.open('rb')) for p in {p for p,_,_ in locations.values()}}
        with tmp.open('wb') as f:
            for sample in samples:
                if sample['id'] in locations:
                    p,offset,n=locations[sample['id']];handles[p].seek(offset);f.write(handles[p].read(n))
    tmp.replace(target)

async def run(cfg,manifest):
    preflight,run_cell,recover_journal,run_identity,ChatClient,summarize=runtime()
    graph,all_data=preflight(cfg);data={n:all_data[n] for n in COUNTS}
    if load(OUT/'control.json').get('paused'):raise RuntimeError('This run is paused; explicit resume authorization is required')
    if not os.environ.get(cfg['backbones'][BACKBONE]['api_key_env']):raise RuntimeError('Missing process-local API credential')
    acquire_lock()
    prior_state=OUT/'process_state.json'
    if prior_state.exists():
        archive=OUT/'state_history'/('before_'+str(os.getpid())+'.json')
        archive.parent.mkdir(exist_ok=True)
        if not archive.exists():archive.write_bytes(prior_state.read_bytes())
    state={'status':'running','pid':os.getpid(),'started_at':now(),'source_version':'r19','datasets':list(COUNTS),'total':sum(COUNTS.values())}
    write(OUT/'process_state.json',state)
    with (OUT/'epochs.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({**state,'controller_sha256':sha(Path(__file__)),'maximum_api_concurrency':manifest['maximum_api_concurrency']})+'\n')
    scope_path=ROOT/'configs/gpt56_sol_scope.json';scope=load(scope_path)
    if not (OUT/'previous_scope.json').exists():(OUT/'previous_scope.json').write_bytes(scope_path.read_bytes())
    scope.update(active_run=str(OUT),frozen_model_config=str(OUT/'source_snapshot/configs/run.json'),control_file=str(OUT/'control.json'))
    write(scope_path,scope)
    shards=[];prior_usage=[]
    for name,ss in data.items():
        for index,start in enumerate(range(0,len(ss),SHARD_SIZE)):
            rows=ss[start:start+SHARD_SIZE];folder=OUT/'shards'/name/f'{index:03d}'
            journal=folder/BACKBONE/name/'predictions.jsonl';recover_journal(journal)
            usage=journal.parent/'api_usage.json'
            if usage.exists():prior_usage.extend(load(usage))
            c=deepcopy(cfg);c['output_dir']=str(folder)
            shards.append({'dataset':name,'index':index,'samples':rows,'ids':{s['id'] for s in rows},'journal':journal,'config':c})
    shards.sort(key=lambda s:(s['index'],list(COUNTS).index(s['dataset'])))
    write(OUT/'shards_manifest.json',{'shard_size':SHARD_SIZE,'shards':[{'dataset':s['dataset'],'index':s['index'],'ids':sorted(s['ids'])} for s in shards]})
    stop=asyncio.Event();finished=asyncio.Event();reason={};clients=[];locks={};active=set();reader=JournalIndex()
    def request_stop(kind,**details):
        if not stop.is_set():reason.update(kind=kind,**details)
        stop.set()
    init=ChatClient.__init__
    def client_init(self,*a,**kw):
        init(self,*a,**kw);self.locks=locks;clients.append(self)
        async def service_hook(response):
            if response.status_code<400:return
            await response.aread()
            try:detail=response.json().get('error',{})
            except (ValueError,AttributeError):detail={'message':'non-json service error'}
            if isinstance(detail,dict):detail={k:detail[k] for k in ('code','type','message') if k in detail}
            safe=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',json.dumps(detail,ensure_ascii=False).replace(self.api_key,'[REDACTED]'))
            with (OUT/'service_errors.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'at':now(),'status':response.status_code,'detail':json.loads(safe)},ensure_ascii=False)+'\n')
            if response.status_code in {401,402,403}:request_stop('service_rejected',http_status=response.status_code)
        self.http.event_hooks['response']=[service_hook]
    ChatClient.__init__=client_init
    def progress():
        reader.poll(shards);metrics={}
        for name,rows in data.items():
            pp=reader.rows[name];m=summarize(rows,list(pp.values()),cfg['evaluation']['unspecified_decimals'],cfg['evaluation']['precision_policy'])
            negatives=[s for s in rows if s['unanswerable'] and s['id'] in pp]
            m['processed_total_accuracy']=100*m['correct']/len(pp) if pp else None
            m['processed_abstention_accuracy']=100*sum(pp[s['id']]['status']=='abstained' for s in negatives)/len(negatives) if negatives else None
            metrics[name]=m
        records=[r for c in clients for r in c.records]
        obj={'updated_at':now(),'pid':os.getpid(),'status':state['status'],'source_version':'r19','total':sum(COUNTS.values()),
             'completed':sum(m['predictions'] for m in metrics.values()),'errors':sum(m['errors'] for m in metrics.values()),'datasets':metrics,
             'active_shards':sorted(active),'successful_operator_responses':len(prior_usage)+len(records),'new_responses_this_process':sum(not r['cached'] for r in records),
             'note':'Processed accuracies are provisional; full-denominator metrics include missing samples. No error is a successful abstention.'}
        write(OUT/'progress.json',obj)
        fmt=lambda x:'—' if x is None else f'{x:.2f}%'
        lines=['# GBFR R19 全量实时进度','',f"状态：{state['status']}；已保存 {obj['completed']} / {obj['total']}；技术错误 {obj['errors']}。",f"更新时间（UTC）：{obj['updated_at']}",'',
            '| 数据集 | 已保存 / 总数 | 已处理题正确率 | 已处理不可回答题拒答率 | 技术错误 |','|---|---:|---:|---:|---:|']
        for n,m in metrics.items():lines.append(f"| {n} | {m['predictions']}/{m['n']} | {fmt(m['processed_total_accuracy'])} | {fmt(m['processed_abstention_accuracy'])} | {m['errors']} |")
        lines+=['','上述是未完成实验的进度，不是最终指标。结果逐题落盘；进程结束时生成 results.md。']
        (OUT/'progress.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        write(OUT/'process_state.json',{**state,'heartbeat_at':obj['updated_at'],'completed':obj['completed'],'errors':obj['errors']})
        return obj
    async def heartbeat():
        while not finished.is_set():
            try:
                progress()
                if load(OUT/'control.json').get('paused'):request_stop('user_paused')
            except Exception as exc:request_stop('progress_error',error_type=type(exc).__name__,message=str(exc))
            try:await asyncio.wait_for(finished.wait(),timeout=15)
            except asyncio.TimeoutError:pass
    sem=asyncio.Semaphore(PARALLEL_SHARDS)
    async def work(s):
        async with sem:
            if stop.is_set():return
            tag=s['dataset']+'/'+str(s['index']);active.add(tag)
            try:await run_cell(s['config'],graph,s['dataset'],s['samples'],BACKBONE)
            except Exception as exc:request_stop('worker_error',shard=tag,error_type=type(exc).__name__,message=str(exc))
            finally:active.discard(tag)
    tasks=[];pump=None;stopper=None
    try:
        progress();pump=asyncio.create_task(heartbeat())
        tasks=[asyncio.create_task(work(s)) for s in shards];batch=asyncio.gather(*tasks,return_exceptions=True)
        stopper=asyncio.create_task(stop.wait())
        await asyncio.wait([batch,stopper],return_when=asyncio.FIRST_COMPLETED)
        if stop.is_set():
            for t in tasks:
                if not t.done():t.cancel()
        await batch
    except BaseException as exc:
        request_stop('controller_interrupted',error_type=type(exc).__name__)
        for t in tasks:
            if not t.done():t.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
    finally:
        finished.set()
        if stopper:stopper.cancel();await asyncio.gather(stopper,return_exceptions=True)
        if pump:await pump
        ChatClient.__init__=init
    try:
        state['status']='merging';progress()
        for name,rows in data.items():
            target=OUT/BACKBONE/name/'predictions.jsonl';merge_journals(shards,name,rows,target)
            usages=[]
            for s in shards:
                if s['dataset']==name and (s['journal'].parent/'api_usage.json').exists():usages.extend(load(s['journal'].parent/'api_usage.json'))
            write(target.parent/'api_usage.json',usages)
            write(target.parent/'run.json',{'identity':run_identity(cfg,BACKBONE,name),'sample_count':len(rows),'source_version':'r19'})
        p=progress();complete=p['completed']==p['total']
        state['status']=('completed_with_errors' if p['errors'] else 'completed') if complete else ('paused' if reason.get('kind')=='user_paused' else 'interrupted')
        state.update(finished_at=now(),stop_reason=reason or None,exit_code=0 if complete and not p['errors'] else 1)
        p=progress()
        for n,m in p['datasets'].items():
            m['fixed_two_decimal_diagnostic']=summarize(data[n],list(reader.rows[n].values()),2,'fixed')
            write(OUT/BACKBONE/n/'metrics.json',m)
        result={'finished_at':state['finished_at'],'status':state['status'],'source_version':'r19','model':'gpt-5.6-sol','total':p['total'],
            'completed':p['completed'],'datasets':p['datasets'],'stop_reason':reason or None,'full_run_authorized':True}
        write(OUT/'results.json',result)
        lines=['# GBFR R19 全量实验结果','',f"状态：{state['status']}；记录 {p['completed']}/{p['total']}。",'',
            '| 数据集 | 已处理 | Total Acc. | Abst. Acc. | 论文 GPT-5 Total / Abst. 参考 | 技术错误 |', '|---|---:|---:|---:|---:|---:|']
        refs={'FinQA':'84.98% / 98.80%','TAT-QA':'95.75% / 96.69%'}
        for n,m in p['datasets'].items():lines.append(f"| {n} | {m['predictions']}/{m['n']} | {m['total_accuracy']:.2f}% | {m['abstention_accuracy']:.2f}% | {refs[n]} | {m['errors']} |")
        lines+=['','不完整结果使用完整计划分母，不能当作已完成效果。错误不计正确拒答。',
            '当前骨干由用户指定为 GPT-5.6 Sol，资产为冻结重建版本，分母与论文有差异；参考值不代表同配置精确复现。']
        (OUT/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        print(json.dumps({'status':state['status'],'completed':p['completed'],'total':p['total'],'errors':p['errors']},ensure_ascii=False),flush=True)
        return state['exit_code']
    finally:
        lock=OUT/'run.lock'
        if lock.exists() and load(lock).get('pid')==os.getpid():lock.unlink()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['prepare','check','run','status'],default='check');args=parser.parse_args()
    if args.mode=='status':
        print(json.dumps(load(OUT/'progress.json'),ensure_ascii=False));return
    cfg,manifest=prepare()
    if args.mode in {'prepare','check'}:
        preflight,*_=runtime();_,datasets=preflight(cfg)
        print(json.dumps({'ready':True,'source_version':'r19','counts':{n:len(datasets[n]) for n in COUNTS},'total':sum(COUNTS.values()),
            'maximum_api_concurrency':manifest['maximum_api_concurrency'],'api_calls':0,'out':str(OUT)},ensure_ascii=False));return
    sys.exit(asyncio.run(run(cfg,manifest)))

if __name__=='__main__':main()
