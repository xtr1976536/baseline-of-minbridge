"""Read-only diagnosis of a frozen validation round; never calls a model."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def rows(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []

def main(round_name):
    out=ROOT/'runs/gbfr_v3_validation'/round_name
    sys.path.insert(0,str(out/'source_snapshot'))
    from gbfr.metrics import correct,summarize
    config=json.loads((out/'configuration.json').read_text(encoding='utf-8'))
    policy=config['evaluation'].get('precision_policy','fixed')
    report={'at':datetime.now(timezone.utc).isoformat(),'round':round_name,'precision_policy':policy,'full_run_authorized':False,'datasets':{}}
    lines=['# 固定小样本逐题诊断','',f'轮次：{round_name}；精度口径：{policy}；本脚本仅读取结果，不调用 API、不重跑失败题。','']
    for name in ['FinQA','TAT-QA']:
        samples=rows(ROOT/'data/validation/gbfr_v3'/(name+'.jsonl'))
        predictions=rows(out/'GPT-5.6 Sol'/name/'predictions.jsonl')
        by_id={p['sample_id']:p for p in predictions}
        counts=Counter();warnings=Counter();failures=[]
        for s in samples:
            p=by_id.get(s['id'])
            if p is None:counts['missing']+=1;continue
            events=p.get('trace',{}).get('events',[])
            for e in events:
                if e['operator']=='evidence_audit':warnings[e.get('reason','unknown')]+=1
            ok=correct(p,s,config['evaluation']['unspecified_decimals'],policy)
            if ok:counts['correct_abstention' if s['unanswerable'] else 'correct_answer']+=1;continue
            category=('technical_error' if p['status']=='error' else 'false_abstention' if p['status']=='abstained'
                      else 'false_answer_on_counterfactual' if s['unanswerable'] else 'incorrect_numeric_answer')
            counts[category]+=1
            failures.append({'id':s['id'],'question':s['question'],'gold':s['answer'],'unanswerable':s['unanswerable'],
                'status':p['status'],'value':p.get('value'),'meta':p.get('meta',{}),'category':category,
                'error':p.get('error'),'reason':p.get('reason'),
                'oes_missing':[e['response'].get('notes') for e in events if e['operator']=='OES' and not e['response'].get('found')],
                'oqa':next((e['response'] for e in events if e['operator']=='OQA'),None)})
        metrics=summarize(samples,predictions,config['evaluation']['unspecified_decimals'],policy)
        report['datasets'][name]={'metrics':metrics,'categories':dict(counts),'supplementary_audit_warnings':dict(warnings),
            'fixed_two_decimal_diagnostic':summarize(samples,predictions,2,'fixed'),'failed_cases':failures}
        lines+=[f'## {name}','',f"已处理 {metrics['predictions']}/{metrics['n']}；正确 {metrics['correct']}；Total Acc. {metrics['total_accuracy']:.2f}%；正确拒答 {metrics['correct_abstentions']}/{metrics['unanswerable']}；技术错误 {metrics['errors']}。",'',
                '| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类别 |','|---|---|---|---|---|---|']
        for f in failures:
            esc=lambda x:str(x).replace('|','\\|').replace('\n',' ')
            lines.append('| '+' | '.join(esc(f[k]) for k in ['id','question','status','value','gold','category'])+' |')
        lines.append('')
    (out/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({n:{'metrics':d['metrics'],'categories':d['categories']} for n,d in report['datasets'].items()},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--round',default='r4');args=p.parse_args()
    if not args.round.replace('_','').replace('-','').isalnum():p.error('Invalid round name')
    main(args.round)
