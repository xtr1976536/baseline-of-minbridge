"""Only the pre-frozen 66-case repair validation; never starts the full run."""
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
VALIDATION=ROOT/'data/validation/gbfr_v3'
PYTHON=ROOT/'gbfr'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def source_hashes():
    return {p.relative_to(PYTHON).as_posix():sha(p) for p in PYTHON.rglob('*') if p.suffix in {'.py','.txt'} and '__pycache__' not in p.parts}

def prepare(args):
    manifest_path=VALIDATION/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['total']!=66 or set(manifest['datasets'])!={'FinQA','TAT-QA'}:raise RuntimeError('Wrong validation scope')
    for name,item in manifest['datasets'].items():
        if item['n']!=33 or sha(VALIDATION/(name+'.jsonl'))!=item['sha256']:raise RuntimeError('Validation set changed')
    config=json.loads((ROOT/'configs/gpt56_sol.json').read_text(encoding='utf-8'))
    for key in ['graph','data_dir','output_dir','cache_dir','asset_lock']:
        config[key]=str((ROOT/config[key]).resolve())
    out=ROOT/'runs/gbfr_v3_validation'/args.round
    snapshot=out/'source_snapshot'
    hashes=source_hashes()
    frozen_path=out/'validation_run.json'
    if frozen_path.exists():
        old=json.loads(frozen_path.read_text(encoding='utf-8'))
        if old['source_sha256']!=hashes or old['validation_manifest_sha256']!=sha(manifest_path):
            raise RuntimeError('This round belongs to a different implementation. Preserve it and use a new round name.')
    elif args.mode=='run':
        snapshot.mkdir(parents=True,exist_ok=False)
        shutil.copytree(PYTHON,snapshot/'gbfr',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        save(frozen_path,{'created_at':datetime.now(timezone.utc).isoformat(),'mode':'small-validation-only',
            'full_run_authorized':False,'n':66,'source_sha256':hashes,'validation_manifest_sha256':sha(manifest_path),
            'operator_bodies':'Appendix F unchanged; explicit format slots, generic OQA examples for the unspecified example slot, and representation adapters documented separately.'})
    if args.mode=='run':sys.path.insert(0,str(snapshot))
    else:sys.path.insert(0,str(ROOT))
    config.update(output_dir=str(out),cache_dir=str(ROOT/'runs/cache_gbfr_v3'),example_concurrency=4,
        validation_manifest_sha256=sha(manifest_path))
    if args.reasoning_effort:
        config['backbones']['GPT-5.6 Sol']['parameters']['reasoning_effort']=args.reasoning_effort
    config['backbones']['GPT-5.6 Sol']['concurrency']=4
    config['user_instruction']='User authorized only code repairs and fixed small validation; full run stays paused.'
    return config,manifest,out

async def main(args,config,manifest,out):
    from gbfr.runner import preflight,run_cell,recover_journal
    from gbfr.llm import ChatClient
    from gbfr.metrics import summarize
    from gbfr.types import dumps
    graph,all_data=preflight(config)
    selected={}
    for name in manifest['datasets']:
        rows=[json.loads(s) for s in (VALIDATION/(name+'.jsonl')).read_text(encoding='utf-8').splitlines()]
        native={s['id']:s for s in all_data[name]}
        if len(rows)!=33 or any(native.get(s['id'])!=s for s in rows):raise RuntimeError('Validation differs from frozen benchmark inputs or labels')
        if sum(s['unanswerable'] for s in rows)!=3:raise RuntimeError('Validation class balance changed')
        selected[name]=rows
    if args.mode=='check':
        print(dumps({'ready':True,'n':66,'datasets':{n:{'original':30,'counterfactual':3} for n in selected},'api_calls':0,'full_run_authorized':False}))
        return
    config_path=out/'configuration.json'
    if config_path.exists() and json.loads(config_path.read_text(encoding='utf-8'))!=config:
        raise RuntimeError('This round already has a different frozen configuration; use a new round name.')
    if not config_path.exists():save(config_path,config)
    if args.retry_service_errors:
        for name in selected:
            path=out/'GPT-5.6 Sol'/name/'predictions.jsonl'
            rows=recover_journal(path);retry=[p for p in rows if p.get('error_type')=='APIError' and
                (re.search(r'HTTP (?:401|402|403|429|5\d\d)',p.get('error','')) or p.get('error','').startswith('Transport failure'))]
            if not retry:continue
            archive=out/'service_attempts'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')/(name+'.jsonl')
            archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(path.read_bytes())
            ids={p['sample_id'] for p in retry};path.write_text(''.join(dumps(p)+'\n' for p in rows if p['sample_id'] not in ids),encoding='utf-8')
    original_init=ChatClient.__init__;shared_locks={}
    def traced_init(self,*a,**kw):
        original_init(self,*a,**kw);self.locks=shared_locks
        async def response_hook(response):
            if response.status_code<400:return
            await response.aread()
            try:body=response.json();detail=body.get('error',body)
            except ValueError:detail={'message':response.text[:500]}
            if isinstance(detail,dict):detail={k:detail[k] for k in ('code','type','message','detail') if k in detail}
            safe=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',json.dumps(detail,ensure_ascii=False).replace(self.api_key,'[REDACTED]'))
            with (out/'service_errors.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(dumps({'at':datetime.now(timezone.utc).isoformat(),'status_code':response.status_code,'error':json.loads(safe)})+'\n')
        self.http.event_hooks['response']=[response_hook]
    ChatClient.__init__=traced_init
    state={'pid':os.getpid(),'status':'running','started_at':datetime.now(timezone.utc).isoformat(),'n':66,'full_run_authorized':False}
    save(out/'state.json',state)
    failures=[];tasks=[]
    async def one(name,rows):
        try:await run_cell(config,graph,name,rows,'GPT-5.6 Sol')
        except Exception as exc:
            failures.append({'dataset':name,'type':type(exc).__name__,'message':str(exc)})
            for task in tasks:
                if task is not asyncio.current_task() and not task.done():task.cancel()
    try:
        tasks=[asyncio.create_task(one(name,rows)) for name,rows in selected.items()]
        await asyncio.gather(*tasks,return_exceptions=True)
    finally:
        results={}
        for name,rows in selected.items():
            preds=recover_journal(out/'GPT-5.6 Sol'/name/'predictions.jsonl')
            metrics=summarize(rows,preds,config['evaluation']['unspecified_decimals'],config['evaluation'].get('precision_policy','fixed'))
            metrics['fixed_two_decimal_diagnostic']=summarize(rows,preds,2,'fixed')
            reference=manifest['reference'][name]
            metrics['reference']=reference
            metrics['passes']=metrics['complete'] and metrics['total_accuracy']>=reference['total_accuracy'] and metrics['abstention_accuracy']>=reference['abstention_accuracy']
            results[name]=metrics
        passed=all(d['passes'] for d in results.values())
        result={'checked_at':datetime.now(timezone.utc).isoformat(),'model':'gpt-5.6-sol','n':66,
            'model_parameters':config['backbones']['GPT-5.6 Sol']['parameters'],
            'full_run_authorized':False,'all_passed':passed,'failures':failures,'datasets':results,
            'rule':'All fixed cases must be processed with zero technical errors. Both Total Acc. and Abst. Acc. must reach Table 1 GPT-5 GBFR values for each dataset. No gold-conditioned retries or sample replacement.',
            'scope_limit':'Small local validation does not establish full-benchmark replication or identity with the unpublished expert FMKG.'}
        save(out/'results.json',result)
        lines=['# GBFR 小规模验证','',f"固定 66 题；骨干 GPT-5.6 Sol；验收：{'通过' if passed else '未通过'}。",'',
            '| 数据集 | 已处理 / 总数 | 正确 | Total Acc. | 论文门槛 | Abst. Acc. | 论文门槛 | 错误 | 通过 |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---|']
        for name,m in results.items():
            lines.append(f"| {name} | {m['predictions']} / {m['n']} | {m['correct']} | {m['total_accuracy']:.2f}% | {m['reference']['total_accuracy']:.2f}% | {m['abstention_accuracy']:.2f}% | {m['reference']['abstention_accuracy']:.2f}% | {m['errors']} | {'是' if m['passes'] else '否'} |")
        lines+=['','技术/服务错误计错，不算正确拒答。未处理题保留在分母中。',
            '精度口径：问题显式要求优先；否则按金标的展示小数位同步舍入。论文未明确唯一默认位数，此为公开记录的工程约定。',
            '同时报告固定两位小数的敏感性诊断，不隐藏评分口径对成绩的影响。']
        for name,m in results.items():
            lines.append(f"{name} 固定两位诊断 Total Acc.：{m['fixed_two_decimal_diagnostic']['total_accuracy']:.2f}%。")
        lines+=['','全量实验仍保持暂停，未经用户另行通知不启动。']
        (out/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        state.update(status='finished',finished_at=datetime.now(timezone.utc).isoformat(),all_passed=passed,failures=failures)
        save(out/'state.json',state)
        print(dumps(result),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['check','run'],default='check')
    parser.add_argument('--round',default='r1')
    parser.add_argument('--retry-service-errors',action='store_true')
    parser.add_argument('--reasoning-effort',choices=['low','medium','high'])
    args=parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',args.round):parser.error('Invalid round name')
    config,manifest,out=prepare(args)
    asyncio.run(main(args,config,manifest,out))
