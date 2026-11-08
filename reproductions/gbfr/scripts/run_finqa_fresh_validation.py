"""Exactly ten pre-frozen unseen FinQA questions. Never TAT-QA or full run."""
import argparse
import asyncio
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import sys

import run_live_repair_validation as controller
from run_live_repair_validation import load,rows,sha,sources,write,now

ROOT=controller.ROOT
SELECTION=ROOT/'data/validation/gbfr_finqa_r25'
GRAPH=ROOT/'data/assets/fmkg.reconstructed_candidate_v2_conservative.json'
BACKBONE=controller.BACKBONE

def prepare(round_name):
    if not load(ROOT/'runs/gpt56_sol_full_r19/control.json')['paused']:raise RuntimeError('Full must remain paused')
    manifest=load(SELECTION/'manifest.json');ss=rows(SELECTION/'FinQA.jsonl')
    if len(ss)!=10 or sum(s['unanswerable'] for s in ss)!=2 or any(s['dataset']!='FinQA' for s in ss):raise RuntimeError('Exactly eight original and two counterfactual FinQA questions are required')
    if len({s['id'] for s in ss})!=10 or len({(s['question'],s['context']) for s in ss})!=10:raise RuntimeError('Duplicate questions')
    identity={'source_sha256':sources(ROOT/'gbfr'),'controller_sha256':sha(Path(__file__)),
        'operator_controller_sha256':sha(Path(controller.__file__)),
        'selection_manifest_sha256':sha(SELECTION/'manifest.json'),'selection_samples_sha256':sha(SELECTION/'FinQA.jsonl'),
        'graph_sha256':sha(GRAPH),'datasets':['FinQA'],'questions':10,
        'primary_precision_policy':'fixed','primary_decimals':2,'secondary_precision_policy':'reference_display'}
    out=ROOT/'runs/gbfr_e2e_validation'/round_name;version=out/'version.json'
    if version.exists():
        if load(version)['identity']!=identity:raise RuntimeError('Frozen round differs; preserve it and use a new round')
    else:
        out.mkdir(parents=True,exist_ok=True)
        if (out/'source_snapshot').exists():raise RuntimeError('Incomplete preparation must not be overwritten')
        shutil.copytree(ROOT/'gbfr',out/'source_snapshot/gbfr',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (out/'source_snapshot/assets').mkdir();shutil.copyfile(GRAPH,out/'source_snapshot/assets/graph.json')
        shutil.copyfile(__file__,out/'controller_snapshot.py');shutil.copyfile(controller.__file__,out/'operator_controller_snapshot.py')
        cfg=deepcopy(load(ROOT/'configs/gpt56_sol.json'))
        cfg.update(graph=str(out/'source_snapshot/assets/graph.json'),asset_lock=str(out/'asset_lock.json'),data_dir=str(ROOT/'data/main'),
            output_dir=str(out),cache_dir=str(out/'cache'),example_concurrency=4,
            user_instruction='Only ten unseen FinQA questions authorized. No TAT-QA calls, no full experiment.',
            prior_live_rounds_on_selection=[],validation_round=round_name,validation_cohort_scope='fresh FinQA only',
            precision_disclosure='Paper does not specify the universal default precision. Fixed two decimals is the conservative primary implementation choice; reference-display is also reported.')
        cfg['evaluation'].update(precision_policy='fixed',unspecified_decimals=2)
        cfg['backbones'][BACKBONE].update(concurrency=8,cache_only=False)
        cfg['backbones'][BACKBONE]['parameters']['reasoning_effort']='high'
        write(out/'configuration.json',cfg);write(version,{'created_at':now(),'identity':identity,'full_run_authorized':False})
        write(out/'selection.json',manifest)
        shutil.copyfile(SELECTION/'FinQA.jsonl',out/'samples.jsonl')
    if sources(out/'source_snapshot/gbfr')!=identity['source_sha256'] or sha(out/'source_snapshot/assets/graph.json')!=identity['graph_sha256']:raise RuntimeError('Execution snapshot changed')
    sys.path.insert(0,str(out/'source_snapshot'))
    from gbfr.runner import preflight,lock_assets
    cfg=load(out/'configuration.json')
    if not Path(cfg['asset_lock']).exists():lock_assets(cfg,'Independent unseen FinQA-only ten-question validation; no main labels or assets overwritten.')
    graph,native=preflight(cfg);lookup={s['id']:s for s in native['FinQA']}
    if any(lookup.get(s['id'])!=s for s in ss):raise RuntimeError('Selection differs from native FinQA')
    return cfg,graph,{('fresh','FinQA'):ss},out

def review(cfg,selected,out):
    from gbfr.metrics import summarize,correct,unit_contract
    ss=selected[('fresh','FinQA')];p=out/'fresh'/BACKBONE/'FinQA/predictions.jsonl'
    pp=rows(p) if p.exists() else [];by={p['sample_id']:p for p in pp}
    primary=summarize(ss,pp,2,'fixed');reference=summarize(ss,pp,2,'reference_display')
    details=[]
    for s in ss:
        prediction=by.get(s['id'],{})
        details.append({'sample_id':s['id'],'question':s['question'],'gold':s['answer'],'unanswerable':s['unanswerable'],
            'status':prediction.get('status','unprocessed'),'value':prediction.get('value'),'meta':prediction.get('meta'),
            'correct_fixed_two':correct(prediction,s,2,'fixed'),'correct_reference_display':correct(prediction,s,2,'reference_display'),
            'unit_contract':unit_contract(prediction,s),'reason':prediction.get('reason'),'error':prediction.get('error')})
    false_abst=sum(not s['unanswerable'] and by.get(s['id'],{}).get('status')=='abstained' for s in ss)
    result=load(out/'results.json');result.update(datasets_used=['FinQA'],questions_planned=10,
        selection_manifest_sha256=sha(SELECTION/'manifest.json'),primary_fixed_two=primary,secondary_reference_display=reference,
        false_abstentions=false_abst,unit_contract_unresolved=sum(d['unit_contract']['status']=='unresolved' for d in details),
        per_question=details,
        scope_note='Ten pre-frozen previously unused FinQA questions only, initially empty cache. No old prediction/program replay. Precision variants are disclosed; unresolved units never count as verified matches. No TAT-QA or full run.')
    usage=load(out/'api_usage.json');result['request_dataset_tags']=sorted({r.get('dataset') for r in usage if r.get('dataset')})
    result['scoring_precision_is_paper_disclosed']=False
    write(out/'results.json',result)
    raw=out/'results.md'
    if raw.exists():shutil.copyfile(raw,out/'operator_controller_report.md')
    pct=lambda n:'未测' if n is None else f'{n:.2f}%'
    lines=['# FinQA全新10题真实API验证','',
        f"已处理{primary['predictions']}/10；新OQA独立题数{result['fresh_api_questions']}；模型gpt-5.6-sol；仅FinQA。",'',
        '| 评分口径 | Total | Abst. | 原始题误拒 | 技术错误 |',
        '|---|---:|---:|---:|---:|',
        f"| 主报：统一两位 | {pct(primary['total_accuracy'])}（{primary['correct']}/10） | {pct(primary['abstention_accuracy'])}（{primary['correct_abstentions']}/2） | {false_abst}/8 | {primary['errors']} |",
        f"| 并列：参考答案显示位数 | {pct(reference['total_accuracy'])}（{reference['correct']}/10） | {pct(reference['abstention_accuracy'])} | {false_abst}/8 | {reference['errors']} |",'',
        '论文GPT-5 FinQA参考：Total84.98%、Abst.98.80%。骨干、样本分布不同；论文未披露统一默认精度的具体选择，不把任一实现选择声称为唯一原论文口径。',
        f"目标单位无法核实：{result['unit_contract_unresolved']}题；不抹除预测明确单位后记正确，也不删除这些题。",'',
        '精度策略在运行前冻结，两种口径使用同一批预测，不按结果选择较高值。只有明确问题要求精度时才覆盖默认值。',
        '10题在代码完成和API运行前冻结；未按答案/预测筛选，所有失败保留。可回答与反事实为8+2，不等于论文全量比例。',
        '原始选择及新鲜性来源见selection.json；每题来源、数值/元数据、单位诊断和双口径判定见results.json。',
        '缺失/技术错误不当成功拒答，未完成批次不当最终成绩。全量与TAT-QA保持暂停。','',
        '## 未通过或单位未判定题','']
    for d in details:
        if not d['correct_fixed_two']:
            lines.append(f"- {d['sample_id']}：{d['status']}，输出{d['value']}，参考{d['gold']}；单位状态{d['unit_contract']['status']}；{d['reason'] or d['error'] or '见完整证据/程序/精度诊断'}")
    (out/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'fresh_api_questions':result['fresh_api_questions'],'fixed_two':primary,
        'reference_display':reference,'false_abstentions':false_abst,'unit_contract_unresolved':result['unit_contract_unresolved'],
        'request_dataset_tags':result['request_dataset_tags']},ensure_ascii=False),flush=True)

async def main(args):
    cfg,graph,selected,out=prepare(args.round)
    controller.NAMES=['FinQA'];controller.COHORTS=['fresh']
    await controller.run(args,cfg,graph,selected,out)
    if args.mode=='run':review(cfg,selected,out)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['check','run'],default='check');parser.add_argument('--round',default='r25');args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.round):parser.error('Invalid round name')
    asyncio.run(main(args))
