import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=[]
for task in ['finqa','convfinqa','tatqa']:
 p=R/'results'/f'{task}-full-greedy-20261102'
 s=json.loads((p/'summary.json').read_text());v=json.loads((p/'validation.json').read_text())
 assert s['status']=='complete' and v['status']=='PASS'
 rows.append({'dataset':task,'n':s['expected'],'correct':s['correct'],'accuracy_percent':s['accuracy_percent'],'paper_percent':s['paper_reference_percent'],'delta_pp':s['difference_percentage_points'],'run_errors':s['run_errors'],'execution_failures':s['execution_failures'],'f1_percent':s.get('f1_percent')})
out=R/'results/financial-main-summary-20261102.json';out.write_text(json.dumps(rows,indent=2))
report='# PoT金融三数据集主实验汇总（2026-11-02）\n\n实际底座gpt-5.6-sol；原论文Codex。Few-shot greedy，每题单程序。\n\n| 数据集 | 样本数 | 正确 | 本次准确率/EM | 论文Table2 greedy | 差值 |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'
for r in rows:report+=f"| {r['dataset']} | {r['n']} | {r['correct']:g} | {r['accuracy_percent']:.4f}% | {r['paper_percent']:.1f}% | {r['delta_pp']:+.4f} pp |\n"
report+='\n三个数据集均通过完整ID/gold对齐与作者评分脚本复算。所有执行失败保留在完整分母。ConvFinQA按作者代码为dev421最后一问，论文Test标签差异单独注明；TAT-QA为dev1668。更强底座可提高得分，不要求数值贴近论文，不据此修改prompt、评分或样本。\n'
report+=f"\nTAT-QA F1：{rows[-1]['f1_percent']:.4f}%。\n"
report+='\nConvFinQA/TAT-QA初始同时并发出现HTTP429/403，已停止并保留传输失败记录；后以单数据集8并发补齐未生成请求。模型已答错或程序失败的样本不重试。首次接口失败记录与调度变化见各结果目录transport_incident.json和initial_transport_failures.jsonl.gz。\n'
(R/'results/金融主实验汇总_20261102.md').write_text(report);print(report)
