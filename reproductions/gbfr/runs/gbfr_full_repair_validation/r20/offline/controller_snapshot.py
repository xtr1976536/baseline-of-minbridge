"""Replay saved final programs only. This script cannot call a model API.

NOT a full-pipeline fresh API verification: OQA/OES/OMD/Verify are not rerun.
The failure-enriched 40-case set is a debug regression set, not a main score.
"""
import argparse
import asyncio
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'pyproject.toml').is_file() and (p/'data/main').is_dir())
FULL=ROOT/'runs/gpt56_sol_full_r19'
SUBSET=ROOT/'data/validation/gbfr_full_repair_v1'
AUDIT=ROOT/'research/repairs/20261107/full_executor_audit.json'
NAMES=['FinQA','TAT-QA']

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(encoding='utf-8') as f:return [json.loads(line) for line in f if line.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def text_sha(s):return hashlib.sha256(s.encode()).hexdigest()
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def source_hashes(folder):
    return {p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.suffix in {'.py','.txt'} and '__pycache__' not in p.parts}
def compact(p):return {k:deepcopy(p[k]) for k in ('sample_id','status','value','meta','precision','error_type','error','reason') if k in p}


def baseline_worker():
    # A separate fresh interpreter is necessary: frozen metrics imports its
    # own relative units module, rather than the concurrently repaired module.
    sys.path.insert(0,str(FULL/'source_snapshot'))
    from gbfr.metrics import correct,summarize
    payload=json.load(sys.stdin);result={}
    for group,cell in payload['groups'].items():
        rr,pp=cell['samples'],cell['predictions']
        result[group]={'metrics':summarize(rr,pp,payload['decimals'],payload['precision_policy']),
            'correct_by_id':{p['sample_id']:correct(p,s,payload['decimals'],payload['precision_policy']) for p,s in zip(pp,rr)}}
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


def verify_inputs():
    manifest=load(SUBSET/'manifest.json');full_manifest=load(FULL/'full_run_manifest.json')
    cfg_path=FULL/'source_snapshot/configs/run.json';cfg=load(cfg_path)
    if sha(cfg_path)!=full_manifest['configuration_sha256']:raise RuntimeError('Frozen R19 configuration changed')
    frozen=source_hashes(FULL/'source_snapshot/gbfr')
    if frozen!=full_manifest['source_sha256']:raise RuntimeError('Frozen R19 baseline source changed')
    if load(FULL/'control.json').get('paused') is not True:raise RuntimeError('Full experiment must remain paused during this audit')
    subsets={};samples={};predictions={};input_hashes={}
    if manifest['quotas_per_dataset']!={'wrong_answer':6,'false_abstention':6,'technical_error':3,'correct':5}:raise RuntimeError('Diagnostic quotas changed')
    for name in NAMES:
        info=manifest['datasets'][name];path=SUBSET/(name+'.jsonl')
        journal=FULL/'GPT-5.6 Sol'/name/'predictions.jsonl';native=Path(cfg['data_dir'])/(name+'.jsonl')
        if sha(path)!=info['sha256']:raise RuntimeError('Frozen subset changed: '+name)
        if sha(journal)!=info['source_journal_sha256']:raise RuntimeError('Frozen source journal changed: '+name)
        if sha(native)!=full_manifest['datasets_sha256'][name]:raise RuntimeError('Native data changed: '+name)
        all_rows=rows(native);samples[name]={s['id']:s for s in all_rows}
        ss=rows(path);ids=[s['id'] for s in ss]
        selected=[ident for rr in info['ids_by_category'].values() for ident in rr]
        if len(ss)!=20 or info['n']!=20 or len(set(ids))!=20 or set(ids)!=set(selected):raise RuntimeError('Subset IDs changed')
        if any(len(info['ids_by_category'].get(k,[]))!=v for k,v in manifest['quotas_per_dataset'].items()):raise RuntimeError('Category sizes changed')
        if any(s['unanswerable'] for s in ss):raise RuntimeError('This original-only diagnostic set has changed')
        if any(samples[name].get(s['id'])!=s for s in ss):raise RuntimeError('Subset question/data/label differs from native data')
        pp=rows(journal);predictions[name]={p['sample_id']:p for p in pp}
        if len(predictions[name])!=len(pp):raise RuntimeError('Duplicate source prediction')
        if any(ident not in predictions[name] for ident in ids):raise RuntimeError('Selected source prediction missing')
        subsets[name]=ss;input_hashes[name]={'subset_sha256':sha(path),'source_journal_sha256':sha(journal),'native_data_sha256':sha(native)}
    audit=load(AUDIT)
    if len(audit['cases'])!=11:raise RuntimeError('Expected every 11 non-service technical-error cases')
    for c in audit['cases']:
        original=predictions[c['dataset']].get(c['id'])
        if original is None or original.get('error')!=c['original_error'] or original.get('status')!='error':raise RuntimeError('Executor-audit case does not match the original journal')
        for execution in c['executions']:
            if text_sha(execution['program'])!=execution['program_sha256']:raise RuntimeError('Recovered program SHA mismatch')
    return manifest,full_manifest,cfg,subsets,samples,predictions,audit,input_hashes,frozen


def final_program(original,audit_case,frozen_engine_sha):
    events=original.get('trace',{}).get('events',[])
    finals=[(i,e) for i,e in enumerate(events) if e.get('operator')=='OPE.final']
    if len(finals)>1:raise RuntimeError('Multiple final-program events in one source prediction')
    if finals:
        index,event=finals[0]
        return {'program':event['program'],'inputs':deepcopy(event['inputs']),
            'proof':{'method':'stored_OPE.final_event','event_index':index}}
    if audit_case is None:return None
    # The frozen engine has two execute sites. Its metric site always follows
    # an OMD event. With a complete original trace containing no such event,
    # exactly one captured call with v1..vN inputs can only be the final site.
    executions=audit_case.get('executions',[])
    if any(e.get('operator') in {'OMD','OPE.metric'} for e in events) or len(executions)!=1:return None
    e=executions[0];keys=set(e['inputs'])
    if not keys or not all(re.fullmatch(r'v[1-9]\d*',k) for k in keys):return None
    if keys!={'v'+str(i) for i in range(1,len(keys)+1)}:return None
    if not events or events[0].get('operator')!='OQA':return None
    return {'program':e['program'],'inputs':deepcopy(e['inputs']),
        'proof':{'method':'captured_execute_with_frozen_control_flow_proof','engine_sha256':frozen_engine_sha,
            'capture_program_sha256':e['program_sha256'],'capture_count':1,'original_trace_has_OMD_or_metric_execution':False,
            'input_key_contract':'v1..vN; metric execute is preceded by OMD in this frozen engine'}}


async def reexecute(sample,original,audit_case,cfg,frozen_engine_sha):
    from gbfr.executor import execute
    from gbfr.units import asks_for_year,result_meta
    candidate=final_program(original,audit_case,frozen_engine_sha)
    if candidate is None:return compact(original),{'method':'unchanged_no_proven_final_program','model_steps_rerun':False}
    plan=next((e['response'] for e in original.get('trace',{}).get('events',[]) if e.get('operator')=='OQA'),{})
    operator=plan.get('operator')
    trace={'program_sha256':text_sha(candidate['program']),'program':candidate['program'],'inputs':candidate['inputs'],
           'provenance':candidate['proof'],'model_steps_rerun':False,'operator_from_original_plan':operator}
    prediction={'sample_id':sample['id'],'value':None,'meta':{},'precision':original.get('precision',plan.get('precision'))}
    try:
        result=await execute(candidate['program'],candidate['inputs'],cfg['execution_timeout'],
            allow_boolean_result=operator=='compare',allow_year_result=asks_for_year(sample['question']))
        trace['execution']=result
        if result is None:prediction.update(status='abstained',reason='Saved final program returned an undefined value')
        else:
            meta=result['trace'].get('output_meta',{})
            if not isinstance(meta,dict):raise ValueError('Invalid output_meta from saved program')
            effective=result_meta(meta,operator,query=sample['question'])
            if effective!=meta:result['trace']['effective_output_meta']=effective
            prediction.update(status='answered',value=result['value'],meta=effective)
        trace['method']='saved_final_program_reexecution'
    except Exception as exc:
        prediction.update(status='error',error_type=type(exc).__name__,error=str(exc))
        trace.update(method='saved_final_program_reexecution_error',error_type=type(exc).__name__,error=str(exc))
    return prediction,trace


def frozen_scores(groups,cfg):
    payload={'groups':groups,'decimals':cfg['evaluation']['unspecified_decimals'],'precision_policy':cfg['evaluation'].get('precision_policy','fixed')}
    r=subprocess.run([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--baseline-worker'],
        input=json.dumps(payload,ensure_ascii=False),capture_output=True,text=True,encoding='utf-8',cwd=ROOT,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=True)
    return json.loads(r.stdout)


def copy_verified_source(source,target,hashes):
    for name,digest in hashes.items():
        p=target/name;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and sha(p)!=digest:raise RuntimeError('Existing snapshot differs; use another output round')
        if not p.exists():p.write_bytes((source/name).read_bytes())
        if sha(p)!=digest:raise RuntimeError('Code changed while creating offline provenance')


async def main(args):
    manifest,full_manifest,cfg,subsets,native,preds,audit,input_hashes,frozen=verify_inputs()
    if args.check:
        print(json.dumps({'ready':True,'subset_questions':40,'separate_error_diagnostics':11,'api_calls':0,'output_written':False}));return
    current=source_hashes(ROOT/'gbfr');controller=sha(Path(__file__))
    identity={'current_source_sha256':current,'frozen_r19_source_sha256':frozen,'controller_sha256':controller,
        'subset_manifest_sha256':sha(SUBSET/'manifest.json'),'executor_audit_sha256':sha(AUDIT),
        'frozen_configuration_sha256':sha(FULL/'source_snapshot/configs/run.json'),'inputs':input_hashes}
    out=ROOT/'runs/gbfr_full_repair_validation'/args.round/'offline'
    if (out/'version.json').exists() and load(out/'version.json')['identity']!=identity:raise RuntimeError('Offline round already belongs to another code/input identity')
    sys.path.insert(0,str(ROOT))
    from gbfr.metrics import correct,summarize
    audit_by_id={c['id']:c for c in audit['cases']}
    groups={n:{'samples':ss,'predictions':[compact(preds[n][s['id']]) for s in ss]} for n,ss in subsets.items()}
    diagnostics_samples=[native[c['dataset']][c['id']] for c in audit['cases']]
    groups['error_diagnostics']={'samples':diagnostics_samples,'predictions':[compact(preds[c['dataset']][c['id']]) for c in audit['cases']]}
    baseline=frozen_scores(groups,cfg);dataset_results={};records={};diagnostics=[]
    for name in NAMES:
        for category,ids in manifest['datasets'][name]['ids_by_category'].items():
            for ident in ids:
                p=preds[name][ident];ok=baseline[name]['correct_by_id'][ident]
                valid=(ok if category=='correct' else not ok and p['status']=={'wrong_answer':'answered','false_abstention':'abstained','technical_error':'error'}[category])
                if not valid:raise RuntimeError('Frozen category does not match the frozen baseline: '+ident)
    decimals=cfg['evaluation']['unspecified_decimals'];policy=cfg['evaluation'].get('precision_policy','fixed')
    async def one(name,sample):
        original=preds[name][sample['id']];before=compact(original)
        after,proof=await reexecute(sample,original,audit_by_id.get(sample['id']),cfg,frozen['engine.py'])
        return {'id':sample['id'],'question':sample['question'],'frozen_gold':sample['answer'],
            'baseline_prediction':before,'rescored_only_prediction':before,'reexecuted_prediction':after,
            'baseline_correct':baseline[name]['correct_by_id'][sample['id']] if name in NAMES and sample['id'] in baseline[name]['correct_by_id'] else baseline['error_diagnostics']['correct_by_id'][sample['id']],
            'rescored_only_correct':correct(before,sample,decimals,policy),'reexecuted_correct':correct(after,sample,decimals,policy),
            'reexecution':proof}
    for name,ss in subsets.items():
        rr=[await one(name,s) for s in ss];records[name]=rr
        old=[r['baseline_prediction'] for r in rr];new=[r['reexecuted_prediction'] for r in rr]
        dataset_results[name]={'baseline':baseline[name]['metrics'],'rescored_only':summarize(ss,old,decimals,policy),
            'reexecuted':summarize(ss,new,decimals,policy),
            'unchanged_without_final_program':sum(r['reexecution']['method']=='unchanged_no_proven_final_program' for r in rr),
            'original_correct_retained':sum(r['baseline_correct'] and r['reexecuted_correct'] for r in rr),
            'original_correct_regressions':sum(r['baseline_correct'] and not r['reexecuted_correct'] for r in rr)}
    for c,s in zip(audit['cases'],diagnostics_samples):diagnostics.append(await one(c['dataset'],s))
    # Concurrent edits must never be frozen as though one coherent version ran.
    if source_hashes(ROOT/'gbfr')!=current or sha(Path(__file__))!=controller:raise RuntimeError('Code changed during offline replay; no result frozen. Rerun after edits are stable.')
    if sha(AUDIT)!=identity['executor_audit_sha256']:raise RuntimeError('Program audit changed during replay')
    for name,h in input_hashes.items():
        if sha(FULL/'GPT-5.6 Sol'/name/'predictions.jsonl')!=h['source_journal_sha256']:raise RuntimeError('Full journal changed during replay')
    out.mkdir(parents=True,exist_ok=True)
    copy_verified_source(ROOT/'gbfr',out/'source_snapshot/gbfr',current)
    copy_verified_source(FULL/'source_snapshot/gbfr',out/'frozen_r19_source/gbfr',frozen)
    script=out/'controller_snapshot.py'
    if script.exists() and sha(script)!=controller:raise RuntimeError('Controller snapshot differs')
    if not script.exists():script.write_bytes(Path(__file__).read_bytes())
    save(out/'version.json',{'created_at':datetime.now(timezone.utc).isoformat(),'identity':identity})
    result={'created_at':datetime.now(timezone.utc).isoformat(),'api_requests':0,'questions':40,'separate_error_diagnostics':11,
        'full_run_paused':True,'full_pipeline_fresh_api_verification':False,'model_replanning_performed':False,
        'sample_distribution':'Failure-enriched debug regression; not a paper-distribution main-experiment score.',
        'modes':{'baseline':'Original predictions scored using frozen R19 metrics AND units in a fresh interpreter.',
            'rescored_only':'Exactly original outputs, scored by current metrics; no output/metadata rewrite.',
            'reexecuted':'Only saved proven OPE.final programs and original inputs executed locally, with current output representation/unit adapters. No new OQA/OES/OMD/Verify.'},
        'datasets':dataset_results,'error_diagnostics':diagnostics}
    save(out/'results.json',result)
    for name,rr in records.items():save(out/(name+'.cases.json'),rr)
    lines=['# 全量错误修复：离线复验','',
        '**NOT full-pipeline fresh API verification. 0 API；不重规划、不重取证。**',
        '固定40题为失败富集调试集，不是论文主实验分布；不得把以下分数称为真实端到端准确率。',
        '原误拒且无最终程序的样本保持原预测；不补数值、不挑答案。技术错误仍是失败，不能算正确拒答。','',
        '| 数据集 | 模式 | 正确 / 20 | 该调试集得分 | 技术错误 | 误拒答 |', '|---|---|---:|---:|---:|---:|']
    for name,rr in records.items():
        for mode in ['baseline','rescored_only','reexecuted']:
            m=dataset_results[name][mode];prediction_key='reexecuted_prediction' if mode=='reexecuted' else 'baseline_prediction'
            false_abst=sum(r[prediction_key]['status']=='abstained' for r in rr)
            lines.append(f"| {name} | {mode} | {m['correct']}/20 | {m['total_accuracy']:.2f}% | {m['errors']} | {false_abst} |")
    lines+=['','本集合无反事实题，因此拒答准确率未测，不能写成0%或100%。','',
        'baseline 使用冻结 R19 的评分及单位代码；rescored_only 的变化只说明评分适配差异；reexecuted 的变化才包含保存程序的格式/输出类型适配。',
        '当前新的规划/证据提示词没有在本复验中被模型运行，其效果仍待真实API验证。','',
        '## 另列11个非服务技术错误','',
        '这些案例与40题有重叠，不能当作额外11道独立题合并计分。',
        '| 案例 | 原错误 | 新执行状态 / 值 | 当前评分正确 |', '|---|---|---|---|']
    for r in diagnostics:
        p=r['reexecuted_prediction'];esc=lambda x:str(x).replace('|','\\|').replace('\n',' ')
        lines.append('| '+' | '.join(esc(x) for x in [r['id'],r['baseline_prediction'].get('error'),str(p['status'])+' / '+str(p.get('value')),r['reexecuted_correct']])+' |')
    lines+=['','原始程序、inputs、SHA、阶段证明和输出适配trace在 cases / results JSON中保留。',
        '读前验证了子集SHA、源日志SHA、冻结R19源码和配置SHA、子集与data/main的逐行相同关系；代码运行中发生修改会拒绝冻结。',
        '全量日志和旧源码均未修改。当前源码与冻结R19评分源码另存，保证新旧口径可复查。']
    (out/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(out),'api_requests':0,'full_pipeline_fresh_api_verification':False,
        'datasets':{n:{m:d[m]['correct'] for m in ['baseline','rescored_only','reexecuted']} for n,d in dataset_results.items()}},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--round',default='r20');parser.add_argument('--check',action='store_true')
    parser.add_argument('--baseline-worker',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.baseline_worker:baseline_worker()
    else:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',args.round):parser.error('Invalid round name')
        asyncio.run(main(args))
