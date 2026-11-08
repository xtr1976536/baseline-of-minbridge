"""Read-only prediction review; never invokes the model or changes labels."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pct(x):return '未测' if x is None else f'{x:.2f}%'

def main(round_name):
    out=ROOT/'runs/gbfr_e2e_validation'/round_name
    sys.path.insert(0,str(out/'source_snapshot'))
    from gbfr.metrics import correct,summarize
    result=load(out/'results.json');cfg=load(out/'configuration.json');version=load(out/'version.json')
    selection=ROOT/'data/validation/gbfr_live_r21';manifest=load(selection/'manifest.json')
    baseline=load(ROOT/'research/repairs/20261107/r21_repair_baseline.json')
    decimals=cfg['evaluation']['unspecified_decimals'];policy=cfg['evaluation']['precision_policy']
    details=[];combined={};regression={}
    cohorts=[c for c in ('evaluation','repair') if c in result['datasets']]
    for dataset in ('FinQA','TAT-QA'):
        combined_samples=[];combined_predictions=[]
        for cohort in ('evaluation','repair'):
            if cohort not in cohorts:continue
            ss=rows(selection/cohort/(dataset+'.jsonl'))
            path=out/cohort/'GPT-5.6 Sol'/dataset/'predictions.jsonl'
            pp=rows(path) if path.exists() else [];by={p['sample_id']:p for p in pp}
            combined_samples+=ss;combined_predictions+=pp
            for s in ss:
                p=by.get(s['id'],{})
                details.append({'cohort':cohort,'dataset':dataset,'sample_id':s['id'],
                    'question':s['question'],'unanswerable':s['unanswerable'],'gold':s['answer'],
                    'status':p.get('status','unprocessed'),'value':p.get('value'),
                    'correct':correct(p,s,decimals,policy),'meta':p.get('meta'),
                    'reason':p.get('reason'),'error':p.get('error'),'error_type':p.get('error_type')})
            if cohort=='repair':
                regression[dataset]={}
                for category,ids in manifest['cohorts'][cohort]['datasets'][dataset]['categories'].items():
                    selected=[s for s in ss if s['id'] in ids];predicted=[p for p in pp if p['sample_id'] in ids]
                    m=summarize(selected,predicted,decimals,policy)
                    m['false_abstentions']=sum(not s['unanswerable'] and by.get(s['id'],{}).get('status')=='abstained' for s in selected)
                    regression[dataset][category]={'baseline':baseline['datasets'][dataset]['categories'][category]['frozen_r20'],'live':m}
        m=summarize(combined_samples,combined_predictions,decimals,policy)
        by={p['sample_id']:p for p in combined_predictions}
        m['false_abstentions']=sum(not s['unanswerable'] and by.get(s['id'],{}).get('status')=='abstained' for s in combined_samples)
        m['answerable_correct']=sum(not s['unanswerable'] and correct(by.get(s['id'],{}),s,decimals,policy) for s in combined_samples)
        reference=result['datasets'][cohorts[0]][dataset]['paper_gpt5_reference']
        m['paper_gpt5_reference']=reference
        m['nominal_difference_pp']={k:m[k]-reference[k] for k in ('total_accuracy','abstention_accuracy')}
        combined[dataset]=m
    receipt=load(ROOT/'runs/gpt56_sol_full_r19/pause_receipt_20261107.json')
    preserved={name:sha(ROOT/'runs/gpt56_sol_full_r19'/'GPT-5.6 Sol'/name/'predictions.jsonl')==digest
               for name,digest in receipt['preserved_journal_sha256'].items()}
    unchanged_source={name:sha(ROOT/'gbfr'/name)==digest for name,digest in version['identity']['source_sha256'].items()}
    frozen_source={name:sha(out/'source_snapshot/gbfr'/name)==digest for name,digest in version['identity']['source_sha256'].items()}
    cache_records=[load(p) for p in (out/'cache'/'GPT-5.6 Sol').glob('*.json')]
    api=load(out/'api_usage.json')
    integrity={'old_journals_unchanged':preserved,'frozen_source_matches_current':all(unchanged_source.values()),
        'frozen_snapshot_intact':all(frozen_source.values()),'current_source_differences':[name for name,ok in unchanged_source.items() if not ok],
        'graph_sha256':sha(out/'source_snapshot/assets/graph.json'),
        'full_remains_paused':load(ROOT/'runs/gpt56_sol_full_r19/control.json')['paused'],
        'model_returned_counts':dict(Counter(str(r.get('model_returned')) for r in cache_records)),
        'api_record_counts':dict(Counter((r['task']+(':cache' if r['cached'] else ':network')) for r in api)),
        'input_tokens':sum(r.get('usage',{}).get('prompt_tokens',0) for r in api if not r['cached']),
        'output_tokens':sum(r.get('usage',{}).get('completion_tokens',0) for r in api if not r['cached'])}
    review={'round':round_name,'run_status':result['status'],'fresh_api_questions':result['fresh_api_questions'],
        'combined_descriptive_only':combined,'regression':regression,'integrity':integrity,'per_question':details}
    (out/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# GBFR真实API修复验证复核','',
        f"轮次{round_name}；真实新OQA独立题数{result['fresh_api_questions']}；完整预测{result['questions_processed']}/{result['questions_planned']}；状态{result['status']}。",'',
        'Total=(可回答题数值正确+不可回答题正确拒答)/所有题；Abst.=不可回答题正确拒答/不可回答题。技术错误按失败计入，不等于拒答。','',
        '## 事前固定抽样20题（仅R21首测前未使用；后续为同题回归）','',
        '| 数据集 | Total | 论文GPT-5 Total | 差值pp | Abst. | 论文GPT-5 Abst. | 差值pp | 误拒 | 技术错误 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in result['datasets'].get('evaluation',{}).items():
        ref=m['paper_gpt5_reference'];a=m['processed_metrics']
        delta=lambda key:'未测' if a[key] is None else f"{a[key]-ref[key]:+.2f}"
        lines.append(f"| {name} | {pct(a['total_accuracy'])} ({a['correct']}/{a['n']}) | {ref['total_accuracy']:.2f}% | {delta('total_accuracy')} | {pct(a['abstention_accuracy'])} ({a['correct_abstentions']}/{a['unanswerable']}) | {ref['abstention_accuracy']:.2f}% | {delta('abstention_accuracy')} | {m['false_abstentions']} | {m['errors']} |")
    lines+=['',f"## 本轮{result['questions_planned']}题描述性汇总（仅包含本轮实际计划的集合）",'',
        '| 数据集 | Total | Abst. | 可回答题正确 | 误拒 | 技术错误 |','|---|---:|---:|---:|---:|---:|']
    for name,m in combined.items():
        lines.append(f"| {name} | {pct(m['total_accuracy'])} ({m['correct']}/{m['n']}) | {pct(m['abstention_accuracy'])} ({m['correct_abstentions']}/{m['unanswerable']}) | {m['answerable_correct']}/{m['n']-m['unanswerable']} | {m['false_abstentions']} | {m['errors']} |")
    lines+=['','## 回归题按修复类别比较','',
        '旧基线是R19真实预测在冻结R20评分下的结果；不是新增API。旧反事实未跑，不补成0或100%。','',
        '| 数据集 | 类别 | 旧正确/已测 | 新正确/已测 | 旧误拒 | 新误拒 |','|---|---|---:|---:|---:|---:|']
    for name,categories in regression.items():
        for category,pair in categories.items():
            a,b=pair['baseline'],pair['live']
            old='未测' if not a['observed_in_r19_full'] else f"{a['correct']}/{a['observed_in_r19_full']}"
            lines.append(f"| {name} | {category} | {old} | {b['correct']}/{b['predictions']} | {a['false_abstentions']} | {b['false_abstentions']} |")
    if not regression:lines+=['','本轮没有重复repair集合，不将旧轮回归预测混入本轮结果。']
    lines+=['','## 未通过题（全部保留）','']
    for d in details:
        if not d['correct']:
            lines.append(f"- {d['cohort']} / {d['sample_id']}：{d['status']}，输出{d['value']}，参考{d['gold']}；{d['reason'] or d['error'] or '需审查证据、口径或最终运算'}")
    lines+=['','## 复核限制与保存','',
        '用户选择GPT-5.6 Sol；论文参考为GPT-5，且使用作者未完整公开的最终图谱。本次为独立保守重建候选。',
        '每个数据集每个集合只有2道不可回答题；100%只代表2/2，无法据此证明达到论文约97–99%的全量拒答能力。',
        'evaluation由固定哈希在R21首测前抽取；后续轮次是同题重复诊断，不是独立未使用评估。repair是故障富集样本。合并值仅作描述，不混合不同代码轮次，也不替代论文主实验。',
        '不按结果换题、删失败、改金标或按正确率重试。上述数值含技术错误；不单报成功调用分数。',
        f"全量保持暂停：{integrity['full_remains_paused']}；旧全量两份journal未改：{all(preserved.values())}；该轮执行快照自身完整：{integrity['frozen_snapshot_intact']}。",
        f"当前工作区与该轮快照一致：{integrity['frozen_source_matches_current']}。工作区可继续发展新版本；本轮真实执行始终采用自身冻结快照。"]
    (out/'review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'run_status':review['run_status'],'fresh_api_questions':review['fresh_api_questions'],'combined':combined,'integrity':integrity},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--round',default='r21');args=parser.parse_args();main(args.round)
