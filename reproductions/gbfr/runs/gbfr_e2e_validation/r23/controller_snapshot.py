"""Exactly 40 frozen questions, real end-to-end API; never the full run.

The evaluation and failure-enriched repair cohorts are reported separately.
Every initial round uses its own empty request cache. Within-round exact
request sharing is allowed; saved old predictions/programs are never seeded.
"""
import argparse
import asyncio
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'pyproject.toml').is_file() and (p/'data/main').is_dir())
DATA=ROOT/'data/validation/gbfr_live_r21'
NAMES=['FinQA','TAT-QA']
COHORTS=['evaluation','repair']
BACKBONE='GPT-5.6 Sol'
REFERENCES={'FinQA':{'total_accuracy':84.98,'abstention_accuracy':98.80},
            'TAT-QA':{'total_accuracy':95.75,'abstention_accuracy':96.69}}
SAMPLE=ContextVar('validation_sample',default=None)
OPERATOR=ContextVar('validation_operator',default=None)

def now():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def append(p,obj):
    with p.open('a',encoding='utf-8') as f:f.write(json.dumps(obj,ensure_ascii=False)+'\n')
def sources(folder):return {p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.suffix in {'.py','.txt'} and '__pycache__' not in p.parts}

def measured_metrics(samples,predictions,decimals,policy):
    """Keep planned coverage separate from measured (including error) outcomes."""
    from gbfr.metrics import summarize,correct
    by={p['sample_id']:p for p in predictions}
    measured=[s for s in samples if s['id'] in by]
    m=summarize(samples,predictions,decimals,policy)
    m['processed_metrics']=summarize(measured,predictions,decimals,policy)
    m['false_abstentions']=sum(not s['unanswerable'] and by.get(s['id'],{}).get('status')=='abstained' for s in samples)
    m['answerable_correct']=sum(not s['unanswerable'] and correct(by.get(s['id'],{}),s,decimals,policy) for s in samples)
    return m

def percentage(value):return '未测' if value is None else f'{value:.2f}%'

def load_selection():
    manifest=load(DATA/'manifest.json');selected={};all_ids=set();all_inputs=set()
    if manifest['total']!=40:raise RuntimeError('Fixed 40-question scope changed')
    for cohort in COHORTS:
        for name in NAMES:
            p=DATA/cohort/(name+'.jsonl');m=manifest['cohorts'][cohort]['datasets'][name]
            if sha(p)!=m['sha256']:raise RuntimeError('Frozen selection changed')
            ss=rows(p)
            if len(ss)!=10 or sum(s['unanswerable'] for s in ss)!=2:raise RuntimeError('Class balance changed')
            for s in ss:
                fingerprint=hashlib.sha256((s['question']+'\0'+s['context']).encode()).hexdigest()
                if s['id'] in all_ids or fingerprint in all_inputs:raise RuntimeError('Duplicate question/data in the fixed suites')
                all_ids.add(s['id']);all_inputs.add(fingerprint)
            selected[(cohort,name)]=ss
    return manifest,selected

def prepare(args):
    if not load(ROOT/'runs/gpt56_sol_full_r19/control.json').get('paused'):raise RuntimeError('Full experiment must remain paused')
    manifest,selected=load_selection();out=ROOT/'runs/gbfr_e2e_validation'/args.round
    graph=(ROOT/args.graph).resolve() if not Path(args.graph).is_absolute() else Path(args.graph).resolve()
    identity={'source_sha256':sources(ROOT/'gbfr'),'controller_sha256':sha(Path(__file__)),
        'selection_sha256':sha(DATA/'manifest.json'),'graph_sha256':sha(graph)}
    version=out/'version.json'
    if version.exists():
        if load(version)['identity']!=identity:raise RuntimeError('Round has a different source/input identity; use a new round')
    else:
        out.mkdir(parents=True,exist_ok=True)
        if (out/'source_snapshot').exists():raise RuntimeError('Incomplete preparation requires review; do not overwrite a snapshot')
        shutil.copytree(ROOT/'gbfr',out/'source_snapshot/gbfr',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (out/'source_snapshot/assets').mkdir();shutil.copyfile(graph,out/'source_snapshot/assets/graph.json')
        shutil.copyfile(__file__,out/'controller_snapshot.py')
        prior_rounds=sorted(p.name for p in out.parent.iterdir() if p!=out and (p/'state.json').exists()
            and (p/'version.json').exists() and load(p/'version.json')['identity']['selection_sha256']==identity['selection_sha256'])
        cfg=deepcopy(load(ROOT/'configs/gpt56_sol.json'))
        for k in ['data_dir']:cfg[k]=str((ROOT/cfg[k]).resolve())
        cfg.update(graph=str(out/'source_snapshot/assets/graph.json'),asset_lock=str(out/'asset_lock.json'),output_dir=str(out),cache_dir=str(out/'cache'),
            example_concurrency=4,user_instruction='User authorized only code repairs and a fixed small real API validation; full experiment remains paused.',
            validation_manifest_sha256=identity['selection_sha256'],validation_round=args.round,
            prior_live_rounds_on_selection=prior_rounds)
        cfg['backbones'][BACKBONE].update(concurrency=8,cache_only=False)
        cfg['backbones'][BACKBONE]['parameters']['reasoning_effort']='high'
        write(out/'configuration.json',cfg)
        write(version,{'created_at':now(),'identity':identity,'full_run_authorized':False,'fresh_cache':str(out/'cache')})
        write(out/'selection.json',{'manifest_sha256':identity['selection_sha256'],'n':40,'full_run_authorized':False,
            'cohorts':manifest['cohorts']})
    if sources(out/'source_snapshot/gbfr')!=identity['source_sha256'] or sha(out/'source_snapshot/assets/graph.json')!=identity['graph_sha256']:raise RuntimeError('Snapshot changed')
    sys.path.insert(0,str(out/'source_snapshot'))
    from gbfr.runner import lock_assets,preflight
    cfg=load(out/'configuration.json')
    if not Path(cfg['asset_lock']).exists():lock_assets(cfg,'Independent small validation candidate; source-only graph reconstruction. Native data and gold unchanged.')
    graph_object,native=preflight(cfg)
    for (_,name),ss in selected.items():
        by={s['id']:s for s in native[name]}
        if any(by.get(s['id'])!=s for s in ss):raise RuntimeError('Question/data/label differs from frozen main data')
    return cfg,graph_object,selected,out

async def run(args,cfg,graph,selected,out):
    from gbfr.engine import GBFR
    from gbfr.llm import ChatClient,APIError
    from gbfr.metrics import summarize
    if args.mode=='check':
        print(json.dumps({'ready':True,'questions':40,'cohorts':COHORTS,'api_calls':0,'graph_sha256':sha(Path(cfg['graph'])),'full_run_authorized':False}));return
    if (out/'state.json').exists():raise RuntimeError('This live round was already attempted; preserve it and use a new round')
    if Path(cfg['cache_dir']).exists() and any(Path(cfg['cache_dir']).rglob('*.json')):raise RuntimeError('A new live round must start with an empty cache')
    state={'pid':os.getpid(),'status':'running','started_at':now(),'questions':40,'full_run_authorized':False}
    write(out/'state.json',state);predictions={key:[] for key in selected};fatal=asyncio.Event();failure={};requests=[];responses=[]
    client=ChatClient(cfg['backbones'][BACKBONE],Path(cfg['cache_dir'])/BACKBONE)
    original_complete=client.complete
    async def complete(task,prompt,*,json_mode=False):
        token=OPERATOR.set(task)
        try:
            text=await original_complete(task,prompt,json_mode=json_mode)
            if client.records:client.records[-1].update(sample_id=(SAMPLE.get() or {}).get('id'),cohort=(SAMPLE.get() or {}).get('cohort'),dataset=(SAMPLE.get() or {}).get('dataset'))
            return text
        finally:OPERATOR.reset(token)
    client.complete=complete
    async def request_hook(request):
        ident=uuid.uuid4().hex;request.extensions['validation_request_id']=ident
        item={'at':now(),'id':ident,'sample':SAMPLE.get(),'operator':OPERATOR.get()};requests.append(item);append(out/'requests.jsonl',item)
    async def response_hook(response):
        item={'at':now(),'request_id':response.request.extensions.get('validation_request_id'),'sample':SAMPLE.get(),'operator':OPERATOR.get(),'http_status':response.status_code}
        responses.append(item);append(out/'responses.jsonl',item)
        if response.status_code>=400:
            await response.aread()
            try:detail=response.json().get('error',{})
            except (ValueError,AttributeError):detail={'message':'non-json service error'}
            if isinstance(detail,dict):detail={k:detail[k] for k in ['code','type','message'] if k in detail}
            safe=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',json.dumps(detail,ensure_ascii=False).replace(client.api_key,'[REDACTED]'))
            append(out/'service_errors.jsonl',{**item,'detail':json.loads(safe)})
            if response.status_code in {401,402,403}:failure.update(kind='service_rejected',http_status=response.status_code);fatal.set()
    client.http.event_hooks={'request':[request_hook],'response':[response_hook]}
    model=GBFR(graph,client,cfg['execution_timeout'],evidence_policy=cfg['evidence_policy']);sem=asyncio.Semaphore(4)
    async def one(cohort,name,sample):
        async with sem:
            if fatal.is_set():return
            token=SAMPLE.set({'id':sample['id'],'cohort':cohort,'dataset':name})
            try:
                try:p=(await model.predict(sample['question'],sample['context'])).to_dict()
                except Exception as exc:
                    p={'status':'error','value':None,'meta':{},'error_type':type(exc).__name__,'error':str(exc),'trace':getattr(exc,'gbfr_trace',{})}
                    if isinstance(exc,APIError) and (getattr(exc,'status_code',None) in {401,402,403,429} or (getattr(exc,'status_code',0) or 0)>=500 or str(exc).startswith('Transport failure')):
                        failure.update(kind='api_failure',message=str(exc));fatal.set()
                p['sample_id']=sample['id'];folder=out/cohort/BACKBONE/name;folder.mkdir(parents=True,exist_ok=True)
                append(folder/'predictions.jsonl',p);predictions[(cohort,name)].append(p)
                print(json.dumps({'cohort':cohort,'dataset':name,'processed':len(predictions[(cohort,name)]),'n':10,'status':p['status']},ensure_ascii=False),flush=True)
            finally:SAMPLE.reset(token)
    dispatch=[]
    # Place counterfactuals early enough to measure rejection if the service stops.
    for i in [0,8,1,2,9,3,4,5,6,7]:
        for cohort in COHORTS:
            for name in NAMES:dispatch.append((cohort,name,selected[(cohort,name)][i]))
    tasks=[];stopper=None
    try:
        tasks=[asyncio.create_task(one(*s)) for s in dispatch];batch=asyncio.gather(*tasks,return_exceptions=True)
        stopper=asyncio.create_task(fatal.wait());await asyncio.wait([batch,stopper],return_when=asyncio.FIRST_COMPLETED)
        if fatal.is_set():
            for t in tasks:
                if not t.done():t.cancel()
        await batch
    finally:
        if stopper:stopper.cancel();await asyncio.gather(stopper,return_exceptions=True)
        write(out/'api_usage.json',client.records);await client.close()
    metrics={};lines=['# GBFR 修复后真实API端到端验证','',f'轮次：{args.round}；固定40题；全量未授权。','',
        'evaluation在R21首测前固定哈希抽取，repair为故障富集回归。后续轮次在同题上重复验证，不能再视为独立未使用题；均非论文全量分布。','',
        '| 集合 | 数据集 | 已处理 | 总准确率 | 论文Total | 拒答正确 | 拒答准确率 | 论文Abst. | 误拒 | 技术错误 |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for cohort in COHORTS:
        metrics[cohort]={}
        for name in NAMES:
            ss=selected[(cohort,name)];pp=predictions[(cohort,name)]
            m=measured_metrics(ss,pp,cfg['evaluation']['unspecified_decimals'],cfg['evaluation']['precision_policy'])
            m['paper_gpt5_reference']=REFERENCES[name];m['fixed_two_decimal_diagnostic']=summarize(ss,pp,2,'fixed');metrics[cohort][name]=m
            measured=m['processed_metrics']
            lines.append(f"| {cohort} | {name} | {m['predictions']}/{m['n']} | {percentage(measured['total_accuracy'])} ({measured['correct']}/{measured['n']}) | {REFERENCES[name]['total_accuracy']:.2f}% | {measured['correct_abstentions']}/{measured['unanswerable']} | {percentage(measured['abstention_accuracy'])} | {REFERENCES[name]['abstention_accuracy']:.2f}% | {m['false_abstentions']} | {m['errors']} |")
    fresh_ids={r['sample_id'] for r in client.records if r['task']=='OQA' and not r['cached'] and r.get('sample_id')}
    total=sum(m['predictions'] for mm in metrics.values() for m in mm.values());complete=total==40 and not failure
    result={'finished_at':now(),'questions_planned':40,'questions_processed':total,'fresh_api_question_ids':sorted(fresh_ids),
        'fresh_api_questions':len(fresh_ids),'http_requests_started':len(requests),'http_responses_received':len(responses),
        'status':'finished' if complete else 'interrupted','failure':failure or None,'full_run_authorized':False,
        'complete_without_technical_errors':complete and all(m['complete'] for mm in metrics.values() for m in mm.values()),
        'prior_live_rounds_on_selection':cfg.get('prior_live_rounds_on_selection',[]),
        'model':'gpt-5.6-sol','datasets':metrics,'graph_sha256':sha(Path(cfg['graph'])),
        'scope_note':'Fresh API validation with an initially empty cache; no old prediction/program replay. Small evaluation sample differs from paper full distribution; repair is failure-enriched. Errors/missing samples never count as correct abstentions.'}
    write(out/'results.json',result)
    lines+=['',f'成功取得新OQA响应的独立题数：{len(fresh_ids)}；已保存预测：{total}/40。',
        '表中按已处理题统计；技术错误算失败，未处理题不冒充已测。未完成或没有处理反事实题时不报告最终效果或拒答率。',
        '骨干为用户指定GPT-5.6 Sol，论文参考为GPT-5；样本构成和冻结重建图谱不等于论文原始全量设置。',
        '所有失败保留，不按结果换题、删题、重试模型答案。全量暂停状态不变。']
    (out/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    state.update(status=result['status'],finished_at=result['finished_at'],questions_processed=total,fresh_api_questions=len(fresh_ids),failure=failure or None);write(out/'state.json',state)
    print(json.dumps({'status':state['status'],'processed':total,'fresh_api_questions':len(fresh_ids),'output':str(out)},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['check','run'],default='check');parser.add_argument('--round',default='r21')
    parser.add_argument('--graph',default='data/assets/fmkg.reconstructed.json');args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.round):parser.error('Invalid round name')
    cfg,graph,selected,out=prepare(args);asyncio.run(run(args,cfg,graph,selected,out))
