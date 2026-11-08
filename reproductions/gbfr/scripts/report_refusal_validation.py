"""Read frozen small-suite results and produce a refusal-focused audit."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def rows(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def write(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main(round_name):
    version=ROOT/'runs/gbfr_refusal_validation'/round_name
    sys.path.insert(0,str(version/'source_snapshot'))
    from gbfr.metrics import correct
    outputs={}
    for suite in ['focus','regression','holdout']:
        out=version/suite
        if not (out/'results.json').exists():continue
        result=json.loads((out/'results.json').read_text(encoding='utf-8'))
        config=json.loads((out/'configuration.json').read_text(encoding='utf-8'))
        selection=json.loads((out/'selection.json').read_text(encoding='utf-8'))
        data=ROOT/'data/validation'/('gbfr_refusal_holdout_v1' if suite=='holdout' else 'gbfr_v3')
        analyses={}
        lines=['# 拒答验证逐题诊断','',f'版本：{round_name}；套件：{suite}；只读分析，0 API 调用。','']
        for name in ['FinQA','TAT-QA']:
            samples={s['id']:s for s in rows(data/(name+'.jsonl'))}
            predictions=rows(out/'GPT-5.6 Sol'/name/'predictions.jsonl')
            pp={p['sample_id']:p for p in predictions};counts=Counter();failures=[];negative=[]
            for ident in selection['ids'][name]:
                s=samples[ident];p=pp.get(ident)
                if p is None:counts['missing']+=1;continue
                good=correct(p,s,config['evaluation']['unspecified_decimals'],config['evaluation'].get('precision_policy','fixed'))
                events=p.get('trace',{}).get('events',[])
                plan=next((e['response'] for e in events if e['operator']=='OQA'),None)
                record={'id':ident,'question':s['question'],'status':p['status'],'value':p.get('value'),'gold':s['answer'],
                        'unanswerable':s['unanswerable'],'error':p.get('error'),'plan':plan,
                        'missing_evidence_reasons':[e['response'].get('notes') for e in events if e['operator']=='OES' and not e['response'].get('found')]}
                if s['unanswerable']:negative.append(record)
                category=('correct_abstention' if s['unanswerable'] else 'correct_answer') if good else (
                    'technical_error' if p['status']=='error' else 'false_abstention' if p['status']=='abstained'
                    else 'false_answer_on_counterfactual' if s['unanswerable'] else 'incorrect_numeric_answer')
                counts[category]+=1
                if not good:failures.append({**record,'category':category})
            usage_path=out/'GPT-5.6 Sol'/name/'api_usage.json'
            usage=json.loads(usage_path.read_text(encoding='utf-8')) if usage_path.exists() else []
            analyses[name]={'metrics':result['datasets'][name],'categories':dict(counts),'counterfactuals':negative,'failed_cases':failures,
                            'api_calls':dict(Counter('cache' if x['cached'] else 'new' for x in usage)),
                            'api_usage_available':usage_path.exists()}
            lines += [f'## {name}','',
                '| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |','|---|---|---|---:|---:|---|']
            for f in failures:
                esc=lambda x:str(x).replace('|','\\|').replace('\n',' ')
                lines.append('| '+' | '.join(esc(f[k]) for k in ['id','question','status','value','gold','category'])+' |')
            lines.append('')
        write(out/'analysis.json',analyses);(out/'analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        outputs[suite]=result
    baseline=json.loads((ROOT/'runs/gbfr_v3_validation/r6/results.json').read_text(encoding='utf-8'))
    lines=['# GBFR 拒答专项修复','',f'代码版本：{round_name}；仅小样本，未启动全量。','',
           '| 集合 | 数据集 | 正确拒答 | 拒答准确率 | 正样本作答 | 正样本正确 | 误拒答 | 技术错误 |',
           '|---|---|---:|---:|---:|---:|---:|---:|']
    for name,m in baseline['datasets'].items():
        lines.append(f"| 修复前同66题 | {name} | {m['correct_abstentions']}/{m['unanswerable']} | {m['abstention_accuracy']:.2f}% | 见原报告 | 见原报告 | 见原报告 | {m['errors']} |")
    for suite,r in outputs.items():
        if suite=='focus':continue
        for name,m in r['datasets'].items():
            lines.append(f"| {suite} | {name} | {m['correct_abstentions']}/{m['unanswerable']} | {m['abstention_accuracy']:.2f}% | {m['answerable_answered']}/{m['answerable_controls']} | {m['answerable_correct']} | {m['false_abstentions']} | {m['errors']} |")
        if r.get('cache_only'):
            lines+=['','本套件为禁止联网的缓存重放；缓存缺失只表示尚未取得该请求的响应，不是模型作答或金融拒答。其不完整指标不能替代真实复验。','']
    lines+=['','原66题与新增holdout分开报告；holdout增加了反事实比例，其 Total Acc. 不冒充论文主实验分布的成绩。',
            '所有输入和金标保留；技术错误不算正确拒答。小样本点估计不证明全量达到同样水平。',
            '精度口径保持上一轮 reference_display；固定两位诊断同时保留。']
    if 'regression' in outputs:
        lines+=['','## 原66题总准确率','']
        for name,m in outputs['regression']['datasets'].items():
            if not m['complete']:
                lines.append(f"{name}：未完成（技术错误 {m['errors']}，缺失 {m['missing']}），不作模型效果结论。")
            else:
                lines.append(f"{name}：{m['total_accuracy']:.2f}%（论文参考 {m['reference']['total_accuracy']:.2f}%）；固定两位诊断 {m['fixed_two_decimal_diagnostic']['total_accuracy']:.2f}%。")
    if (version/'operator_controls/results.json').exists():
        controls=json.loads((version/'operator_controls/results.json').read_text(encoding='utf-8'))
        lines+=['','合成可回答对照（不计入数据集成绩）：']
        for c in controls['synthetic_controls']:
            lines.append(f"- {c['id']}：预测 {c['prediction'].get('value')}，预期 {c['expected']}，{'通过' if c['passed'] else '未通过'}。")
    (version/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write(version/'summary.json',{'baseline_r6':baseline,'suites':outputs,'full_run_authorized':False})
    print(json.dumps({suite:{n:{k:m[k] for k in ['correct_abstentions','unanswerable','abstention_accuracy','false_abstentions','errors','total_accuracy']} for n,m in r['datasets'].items()} for suite,r in outputs.items()},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--round',default='r8');args=p.parse_args()
    if not args.round.replace('_','').replace('-','').isalnum():p.error('Invalid round name')
    main(args.round)
