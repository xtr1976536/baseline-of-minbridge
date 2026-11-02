"""Produce frozen official-format predictions, official CLI cross-check and result report."""
import json,sys,subprocess,collections
sys.dont_write_bytecode=True
from protocol import ROOT,VENDOR,official
OUT=ROOT/'results/finqa-full-greedy-20261102'
def main():
 summary=json.loads((OUT/'summary.json').read_text());validation=json.loads((OUT/'validation.json').read_text())
 assert summary['status']=='complete' and summary['completed']==summary['expected']==1147 and validation['status']=='PASS'
 records=[json.loads(line) for line in (OUT/'predictions.jsonl').read_text().splitlines()];_,_,data,_=official('finqa')
 by_index={r['index']:r for r in records};assert len(by_index)==1147
 official_file=OUT/'official_format.jsonl'
 with official_file.open('w') as f:
  for i,example in enumerate(data):
   r=by_index[i];f.write(json.dumps({**example,'generated':[r.get('code','')],'executed':r.get('executed')},ensure_ascii=False)+'\n')
 result=subprocess.run([sys.executable,'compute_score.py','--inputs',str(official_file)],cwd=VENDOR/'outputs',capture_output=True,text=True)
 (OUT/'official_scorer.txt').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
 printed=float(result.stdout.split('accuracy: ')[-1].strip());assert abs(printed-summary['accuracy_percent']/100)<1e-12
 numeric=[r for r in records if not isinstance(r['gold'],str)];binary=[r for r in records if isinstance(r['gold'],str)]
 failure_counts=collections.Counter()
 for r in records:
  if r['status']=='run_error':failure_counts['transport_or_runtime']+=1
  elif r['execution']['status']!='executed':failure_counts[r['execution'].get('error','no_ans').split(':')[0]]+=1
  elif not r['correct']:failure_counts['executed_wrong_answer']+=1
 detail={'failure_counts':dict(failure_counts),'numeric':{'n':len(numeric),'correct':sum(r['correct'] for r in numeric)},'binary':{'n':len(binary),'correct':sum(r['correct'] for r in binary)},'official_cli_accuracy_matches':True}
 (OUT/'analysis.json').write_text(json.dumps(detail,indent=2))
 acc=summary['accuracy_percent'];delta=summary['difference_percentage_points']
 report=f'''# PoT FinQA完整主实验结果（2026-11-02）

已完成FinQA test全量1147题，few-shot greedy、4-shot、每题单程序，16并发。未启动ConvFinQA/TAT-QA。原提示词和生成/执行/评分设置固定；与原论文不同之处为替代底座及已验收的Chat接口/边界空白兼容。

| 项目 | 本次结果 |
| --- | ---: |
| 样本数 | 1147 |
| 正确 | {summary['correct']} |
| 错误（含执行/运行失败） | {1147-summary['correct']} |
| 准确率 | {acc:.4f}% |
| 论文Table2 PoT-Codex greedy | 64.5% |
| 相对论文差值 | {delta:+.4f}个百分点 |
| API/运行异常 | {summary['run_errors']} |
| 程序执行失败 | {summary['execution_failures']} |
| 输出达到length上限 | {summary['truncated_outputs']} |
| 本轮总耗时 | {summary['elapsed_seconds']/60:.2f}分钟 |

作者outputs/compute_score.py已对全部样本重新评分，与本次统计一致；ID、样本数和gold逐条核验通过。详见validation.json、official_scorer.txt、summary.json、analysis.json。失败样本计入1147分母，没有依据是否答对进行补跑、删除、修复答案或放宽评分。

实际API返回模型gpt-5.6-sol；作者参考code-davinci-002。此差值不能用于归因PoT算法改进，也不是原Codex得分的精确重复。高于论文不意味着实现比作者更好；低于也不单独证明实现错误。当前可证明的是金融FinQA设置在替代底座上完成端到端全量、数据覆盖及作者评分复核。

调用usage：{json.dumps(summary['usage'])}。这是token统计，不等于已核对的实际扣费。

原始请求/响应、usage、程序与逐样本分数在predictions.jsonl；official_format.jsonl供原作者评分器重放。配置包含上游commit、输入及运行脚本SHA256。并发只改变请求调度，不改变每题prompt或采样次数。
'''
 (OUT/'结果报告.md').write_text(report)
 print(report)
if __name__=='__main__':main()
