"""Audit and summarize full frozen denominators, including technical errors."""
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/gpt56_sol_full'
SNAPSHOT=OUT/'source_snapshot'
sys.path.insert(0,str(SNAPSHOT))
from gbfr.data import sha256,write_json
from gbfr.runner import preflight,resolve_paths,recover_journal
from gbfr.metrics import summarize

config=resolve_paths(SNAPSHOT/'configs/run.json')
_,datasets=preflight(config)
scope_path=ROOT/'configs/gpt56_sol_scope.json'
selected=globals().get('SELECTED_DATASETS') or (json.loads(scope_path.read_text(encoding='utf-8'))['datasets'] if scope_path.exists() else list(datasets))
if not selected or len(set(selected))!=len(selected) or set(selected)-set(datasets):raise RuntimeError('Invalid report scope')
datasets={name:datasets[name] for name in selected}
basename='audited_results' if len(selected)==4 else '_'.join(selected)+'_results'
frozen=json.loads((OUT/'full_run_manifest.json').read_text(encoding='utf-8'))
for name,digest in frozen['source_sha256'].items():
    if sha256(SNAPSHOT/name)!=digest:raise RuntimeError('Frozen source mismatch: '+name)
rows=[]
summary={}
for name,samples in datasets.items():
    path=OUT/'GPT-5.6 Sol'/name/'predictions.jsonl'
    predictions=recover_journal(path)
    result=summarize(samples,predictions,config['evaluation']['unspecified_decimals'])
    result['statuses']=dict(Counter(p['status'] for p in predictions))
    result['error_reasons']=dict(Counter(p.get('error','unknown') for p in predictions if p['status']=='error'))
    summary[name]=result
    rows.append((name,result))
overall={key:sum(v[key] for v in summary.values()) for key in ('n','predictions','missing','errors','correct','unanswerable','correct_abstentions')}
overall['total_accuracy']=100*overall['correct']/overall['n']
overall['abstention_accuracy']=100*overall['correct_abstentions']/overall['unanswerable']
all_attempted=overall['missing']==0
result={'checked_at':datetime.now(timezone.utc).isoformat(),'model':'gpt-5.6-sol',
    'all_examples_attempted':all_attempted,'error_free':overall['errors']==0,
    'metrics_status':'final_with_errors_counted_incorrect' if all_attempted else 'incomplete_full_denominator_lower_bounds_not_final_scores',
    'selected_datasets':selected,
    'denominator_policy':f"All {overall['n']} frozen examples in the selected datasets; technical errors and missing predictions are incorrect, never successful abstentions.",
    'comparison_limit':'User-requested backbone and adjusted denominators; not a strict replication of the paper GPT-5 row.',
    'datasets':summary,'overall':overall}
write_json(OUT/(basename+'.json'),result)
lines=['# GBFR / GPT-5.6 Sol '+('实测结果' if all_attempted else '未完成运行记录'),'',
    '本次范围：'+', '.join(selected)+'。',
    f"已处理 {overall['predictions']:,} / {overall['n']:,}；技术错误 {overall['errors']:,}；缺失 {overall['missing']:,}。",
    '全部题目均已尝试。' if all_attempted else '运行未完成；当前不发布全量准确率。原始 JSON 的完整分母数值只表示进度下界，不是最终实验成绩。','']
if all_attempted:
    lines += [
    '| 数据集 | 完整题数 | 已处理 | 正确 | Total Acc. | 正确拒答 / 反事实题 | Abst. Acc. | 技术错误 |',
    '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,r in rows+[('合计',overall)]:
        lines.append(f"| {name} | {r['n']} | {r['predictions']} | {r['correct']} | {r['total_accuracy']:.2f}% | {r['correct_abstentions']} / {r['unanswerable']} | {r['abstention_accuracy']:.2f}% | {r['errors']} |")
else:
    lines += ['| 数据集 | 完整题数 | 当前记录 | 模型输出 | 错误记录 | 无当前记录 |','|---|---:|---:|---:|---:|---:|']
    for name,r in rows+[('合计',overall)]:
        lines.append(f"| {name} | {r['n']} | {r['predictions']} | {r['predictions']-r['errors']} | {r['errors']} | {r['missing']} |")
lines+=['','技术错误不记为正确拒答。原始预测、推理轨迹、API 响应及分片调度记录均保留。',
    '使用用户指定的 GPT-5.6 Sol；图谱为来源可追踪的方法重建，测试集按预先冻结规则调整，与论文 GPT-5 原表不作严格同集合比较。']
(OUT/(basename+'.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
