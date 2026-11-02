"""Audit complete coverage and cross-check official scorers for remaining financial tasks."""
import argparse,json,subprocess,sys,collections
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,official
sys.path.insert(0,str(VENDOR))
from tool import finqa_equal
from eval_tatqa.tatqa_metric import TaTQAEmAndF1

def main():
 p=argparse.ArgumentParser();p.add_argument('--task',choices=['convfinqa','tatqa'],required=True);a=p.parse_args();task=a.task
 out=ROOT/'results'/f'{task}-full-greedy-20261102';summary=json.loads((out/'summary.json').read_text());_,_,data,_=official(task)
 rows=[json.loads(line) for line in (out/'predictions.jsonl').read_text().splitlines()];by_index={r['index']:r for r in rows}
 assert summary['status']=='complete' and len(rows)==len(by_index)==len(data)
 assert set(by_index)==set(range(len(data))) and len({r['id'] for r in rows})==len(data)
 metric=TaTQAEmAndF1();scored=[];roundtrip_differences=[]
 with (out/'official_format.jsonl').open('w') as f:
  for i,example in enumerate(data):
   r=by_index[i];assert r['id']==example.get('id',example.get('question_id')) and r['gold']==example['answer']
   if task=='convfinqa':
    assert r['correct']==finqa_equal(r.get('executed'),example['answer'],False)
    record={**example,'generated':[r.get('code','')],'executed':r.get('executed')}
   else:
    pred=r.get('pred_answer',['']);scale=r.get('pred_scale','')
    individual=TaTQAEmAndF1();individual(example,prediction=pred,pred_scale=scale)
    em,f1,*_=individual.get_overall_metric();assert abs(em-r['correct'])<1e-12
    if abs(f1-r.get('f1',0))>1e-12:roundtrip_differences.append({'index':i,'in_memory_f1':r.get('f1',0),'official_json_f1':f1})
    metric(example,prediction=pred,pred_scale=scale)
    record={**example,'generated':[r.get('code','')],'pred_answer':pred,'pred_scale':scale}
   f.write(json.dumps(record,ensure_ascii=False)+'\n')
 if task=='convfinqa':command=[sys.executable,'compute_score.py','--inputs',str(out/'official_format.jsonl')];cwd=VENDOR/'outputs'
 else:command=[sys.executable,'compute_score_tatqa.py','--inputs',str(out/'official_format.jsonl')];cwd=VENDOR
 result=subprocess.run(command,cwd=cwd,text=True,capture_output=True);assert result.returncode==0,result.stderr
 (out/'official_scorer.txt').write_text(result.stdout+result.stderr)
 printed=float(result.stdout.split('accuracy: ')[-1].strip());assert abs(printed*100-summary['accuracy_percent'])<1e-10
 if task=='tatqa':
  summary['in_memory_f1_percent']=summary['f1_percent'];summary['f1_percent']=metric.get_overall_metric()[1]*100
  summary['f1_policy']='Canonical published JSON + original official scorer; in-memory tuple/list serialization difference retained'
  (out/'summary.json').write_text(json.dumps(summary,indent=2))
  (out/'score_serialization_audit.json').write_text(json.dumps({'em_unchanged':True,'differences':roundtrip_differences,'cause':'Official eval-like prediction conversion may create tuples; JSON converts tuples to lists, changing F1 tokenization. Use published JSON official-scoring result as final.'},indent=2))
 validation={'status':'PASS','expected':len(data),'unique_ids':len(data),'all_ids_and_gold_align':True,'all_stored_scores_match_official_comparator':True,'official_cli_matches':True,'all_failures_in_denominator':True}
 (out/'validation.json').write_text(json.dumps(validation,indent=2))
 categories=collections.defaultdict(lambda:{'n':0,'correct':0,'f1_sum':0})
 failures=collections.Counter()
 for r in rows:
  category=data[r['index']].get('answer_type','binary' if isinstance(r['gold'],str) else 'number')
  c=categories[category];c['n']+=1;c['correct']+=r['correct'];c['f1_sum']+=r.get('f1',0)
  if r['status']=='run_error':failures['run_error']+=1
  elif r['execution']['status']!='executed':failures[r['execution'].get('error','no_ans').split(':')[0]]+=1
  elif not r['correct']:failures['executed_wrong_answer']+=1
 (out/'analysis.json').write_text(json.dumps({'answer_types':dict(categories),'failure_categories':dict(failures)},indent=2))
 report=f"""# PoT {task}全量结果

| 项目 | 结果 |
| --- | ---: |
| 评测样本 | {len(data)} |
| 正确 | {summary['correct']} |
| 准确率/EM | {summary['accuracy_percent']:.4f}% |
| 论文Table2 greedy | {summary['paper_reference_percent']:.1f}% |
| 差值 | {summary['difference_percentage_points']:+.4f}个百分点 |
| 运行错误 | {summary['run_errors']} |
| 程序执行失败 | {summary['execution_failures']} |
| length截断 | {summary['truncated_outputs']} |
| 耗时 | {summary['elapsed_seconds']/60:.2f}分钟 |

固定gpt-5.6-sol、原few-shot prompt、greedy参数与官方执行/评分。原论文为Codex，底座不同可产生更高指标，允许该差异；不以接近旧分数为目标修改参数。初始每数据集16并发并行运行触发HTTP429/403，随后改为单数据集8并发，仅补齐未取得有效输出的传输失败请求；未重试已评分错误答案。失败计入完整分母；官方评分CLI重新计分一致，ID/gold逐条对齐通过。
"""
 if task=='tatqa':report+=f"\n官方F1：{summary['f1_percent']:.4f}%。主对比采用EM，不用F1替代论文准确率。\n"
 else:report+='\n沿用作者实际使用的dev421，每段对话最后一问；论文表中标Test421，与官方数据身份不同，已在split审计逐ID证实。不伪称private test复现。\n'
 (out/'结果报告.md').write_text(report);(out/'.gitignore').write_text('samples/\n*.tmp\n');print(report)
if __name__=='__main__':main()
