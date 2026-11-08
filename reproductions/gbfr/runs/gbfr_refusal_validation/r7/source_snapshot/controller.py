"""Only fixed small refusal suites; no option to run the full benchmark."""
import argparse
import asyncio
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
FOCUS={'FinQA':'FinQA:counterfactual:51','TAT-QA':'TAT-QA:counterfactual:107'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]

def prepare(args):
    folder='gbfr_refusal_holdout_v1' if args.suite=='holdout' else 'gbfr_v3'
    data=ROOT/'data/validation'/folder
    manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    expected={'focus':(2,1,1),'regression':(66,33,3),'holdout':(30,15,10)}[args.suite]
    selected={}
    for name in ['FinQA','TAT-QA']:
        p=data/(name+'.jsonl')
        if sha(p)!=manifest['datasets'][name]['sha256']:raise RuntimeError('Frozen small validation file changed')
        selected[name]=rows(p)
        if args.suite=='focus':selected[name]=[s for s in selected[name] if s['id']==FOCUS[name]]
        if len(selected[name])!=expected[1] or sum(s['unanswerable'] for s in selected[name])!=expected[2]:
            raise RuntimeError('Small validation scope/class balance changed')
    cfg=json.loads((ROOT/'configs/gpt56_sol.json').read_text(encoding='utf-8'))
    for key in ['graph','asset_lock','data_dir','output_dir','cache_dir']:cfg[key]=str((ROOT/cfg[key]).resolve())
    cfg['example_concurrency']=4
    cfg['backbones']['GPT-5.6 Sol']['concurrency']=4
    cfg['backbones']['GPT-5.6 Sol']['parameters']['reasoning_effort']='high'
    cfg['cache_dir']=str(ROOT/'runs/cache_gbfr_v3')
    identity={'suite':args.suite,'manifest_sha256':sha(data/'manifest.json'),
              'ids':{n:[s['id'] for s in rr] for n,rr in selected.items()}}
    cfg['validation_manifest_sha256']=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    version=ROOT/'runs/gbfr_refusal_validation'/args.round
    out=version/args.suite;cfg['output_dir']=str(out)
    cfg['user_instruction']='Only refusal repairs and fixed small validation are authorized; full benchmark remains paused.'
    hashes={p.relative_to(ROOT/'gbfr').as_posix():sha(p) for p in (ROOT/'gbfr').rglob('*') if p.suffix in {'.py','.txt'} and '__pycache__' not in p.parts}
    frozen=version/'version.json'
    version_identity={'source_sha256':hashes,'controller_sha256':sha(Path(__file__))}
    if frozen.exists():
        if json.loads(frozen.read_text(encoding='utf-8'))['identity']!=version_identity:
            raise RuntimeError('This version has different code; preserve it and use a new round name')
    elif args.mode=='run':
        shutil.copytree(ROOT/'gbfr',version/'source_snapshot/gbfr',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        shutil.copyfile(__file__,version/'source_snapshot/controller.py')
        save(frozen,{'created_at':datetime.now(timezone.utc).isoformat(),'identity':version_identity,'full_run_authorized':False})
    sys.path.insert(0,str(version/'source_snapshot') if args.mode=='run' else str(ROOT))
    if args.mode=='run':
        cp=out/'configuration.json'
        if cp.exists() and json.loads(cp.read_text(encoding='utf-8'))!=cfg:raise RuntimeError('Suite configuration changed')
        if not cp.exists():save(cp,cfg)
        save(out/'selection.json',{**identity,'n':expected[0],'full_run_authorized':False})
    return cfg,selected,out,expected[0]

async def main(args,cfg,selected,out,n):
    from gbfr.runner import preflight,run_cell,recover_journal
    from gbfr.llm import ChatClient
    from gbfr.metrics import correct,summarize
    graph,native=preflight(cfg)
    for name,rr in selected.items():
        by_id={s['id']:s for s in native[name]}
        if any(by_id.get(s['id'])!=s for s in rr):raise RuntimeError('Input/label differs from frozen main data')
    if args.mode=='check':
        print(json.dumps({'ready':True,'suite':args.suite,'n':n,'api_calls':0,'full_run_authorized':False}));return
    original_init=ChatClient.__init__;locks={}
    def init(self,*a,**kw):
        original_init(self,*a,**kw);self.locks=locks
        async def hook(response):
            if response.status_code<400:return
            await response.aread()
            try:body=response.json();detail=body.get('error',body)
            except ValueError:detail={'message':'non-json provider error'}
            if isinstance(detail,dict):detail={k:detail[k] for k in ('code','type','message') if k in detail}
            safe=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',json.dumps(detail,ensure_ascii=False).replace(self.api_key,'[REDACTED]'))
            with (out/'service_errors.jsonl').open('a',encoding='utf-8') as f:
                f.write(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'status':response.status_code,'error':json.loads(safe)},ensure_ascii=False)+'\n')
        self.http.event_hooks['response']=[hook]
    ChatClient.__init__=init
    state={'pid':os.getpid(),'status':'running','started_at':datetime.now(timezone.utc).isoformat(),
           'suite':args.suite,'n':n,'full_run_authorized':False};save(out/'state.json',state)
    failures=[];tasks=[]
    async def one(name,rr):
        try:await run_cell(cfg,graph,name,rr,'GPT-5.6 Sol')
        except Exception as exc:
            failures.append({'dataset':name,'type':type(exc).__name__,'error':str(exc)})
            for t in tasks:
                if t is not asyncio.current_task() and not t.done():t.cancel()
    try:
        tasks=[asyncio.create_task(one(name,rr)) for name,rr in selected.items()]
        await asyncio.gather(*tasks,return_exceptions=True)
    finally:
        metrics={};references={'FinQA':{'total_accuracy':84.98,'abstention_accuracy':98.80},
                               'TAT-QA':{'total_accuracy':95.75,'abstention_accuracy':96.69}}
        for name,rr in selected.items():
            pp=recover_journal(out/'GPT-5.6 Sol'/name/'predictions.jsonl');by_id={p['sample_id']:p for p in pp}
            policy=cfg['evaluation'].get('precision_policy','fixed')
            m=summarize(rr,pp,cfg['evaluation']['unspecified_decimals'],policy)
            controls=[s for s in rr if not s['unanswerable']]
            m['answerable_controls']=len(controls)
            m['answerable_answered']=sum(by_id.get(s['id'],{}).get('status')=='answered' for s in controls)
            m['answerable_correct']=sum(correct(by_id.get(s['id'],{}),s,cfg['evaluation']['unspecified_decimals'],policy) for s in controls)
            m['false_abstentions']=sum(by_id.get(s['id'],{}).get('status')=='abstained' for s in controls)
            m['reference']=references[name]
            m['refusal_checks_passed']=m['complete'] and m['abstention_accuracy']>=references[name]['abstention_accuracy'] and (args.suite!='holdout' or m['answerable_answered']==len(controls))
            m['main_thresholds_passed']=args.suite=='regression' and m['complete'] and m['abstention_accuracy']>=references[name]['abstention_accuracy'] and m['total_accuracy']>=references[name]['total_accuracy']
            m['fixed_two_decimal_diagnostic']=summarize(rr,pp,2,'fixed')
            metrics[name]=m
        result={'finished_at':datetime.now(timezone.utc).isoformat(),'suite':args.suite,'n':n,'model':'gpt-5.6-sol',
                'full_run_authorized':False,'failures':failures,'datasets':metrics,
                'refusal_checks_passed':all(m['refusal_checks_passed'] for m in metrics.values()),
                'main_thresholds_passed':all(m['main_thresholds_passed'] for m in metrics.values()),
                'scope_note':'Focus is diagnostic only. Holdout has enriched negatives, so its Total Acc. is not compared as a paper-distribution main score. Errors never count as correct abstentions.'}
        save(out/'results.json',result)
        lines=['# GBFR 拒答小样本验证','',f"套件：{args.suite}；题数：{n}；仅用户指定的 GPT-5.6 Sol；全量未授权。",'',
               '| 数据集 | 已处理 | 正确拒答 | 拒答准确率 | 可回答对照：作答/总数 | 对照正确 | 误拒答 | 错误 |',
               '|---|---:|---:|---:|---:|---:|---:|---:|']
        for name,m in metrics.items():
            lines.append(f"| {name} | {m['predictions']}/{m['n']} | {m['correct_abstentions']}/{m['unanswerable']} | {m['abstention_accuracy']:.2f}% | {m['answerable_answered']}/{m['answerable_controls']} | {m['answerable_correct']} | {m['false_abstentions']} | {m['errors']} |")
        lines+=['',result['scope_note'],'','拒答专项检查：'+('通过' if result['refusal_checks_passed'] else '未通过')+'。',
                '原66题主实验门槛：'+('通过' if result['main_thresholds_passed'] else '未通过或不适用于此套件')+'。']
        (out/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        state.update(status='finished',finished_at=result['finished_at'],refusal_checks_passed=result['refusal_checks_passed'])
        save(out/'state.json',state);print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['check','run'],default='check')
    p.add_argument('--suite',choices=['focus','regression','holdout'],default='regression');p.add_argument('--round',default='r7')
    args=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.round):p.error('Invalid round name')
    cfg,selected,out,n=prepare(args);asyncio.run(main(args,cfg,selected,out,n))
