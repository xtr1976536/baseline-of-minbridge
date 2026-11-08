"""Compare the authorized revised FinanceBench run with its frozen predecessor."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import z3
from vf_repro.common import read_jsonl,write_json,digest
from vf_repro.runner import source_hashes
from vf_repro.scoring import correctness,summarize

ROOT=Path(__file__).resolve().parent.parent
BEFORE=ROOT/'runs/gpt56-sol-final/GPT-5.6-Sol/FinanceBench'
AFTER=ROOT/'runs/financebench-revised-v1/GPT-5.6-Sol/FinanceBench'
PAPER=[
    ('Qwen2.5-7B',10,0,7,34,100.0,78.8,49.3),
    ('Llama-3.1-8B',10,0,12,28,100.0,69.2,58.2),
    ('Qwen3-30B',24,0,8,15,100.0,84.6,77.6),
    ('Fin-o1',32,0,9,12,100.0,83.6,82.1),
    ('Claude Haiku 4.5',28,0,9,13,100.0,83.3,80.6),
    ('GPT-5.5',34,0,6,20,100.0,86.7,70.1),
]


def category(r):
    status=r['result']['status'];correct=r.get('correct')
    if status=='ABSTAIN':return 'Abs'
    if status=='ERROR':return 'Error'
    if correct is None:return 'Unresolved'
    return ('TA' if correct else 'FA') if status=='VERIFIED' else ('FR' if correct else 'TR')


def selected_chunks(record,k=10):
    rankings=[t['reranked'] for t in record['retrieval']];out=[]
    for depth in range(max(map(len,rankings),default=0)):
        for ranking in rankings:
            if depth<len(ranking) and ranking[depth] not in out:out.append(ranking[depth])
            if len(out)==k:return out
    return out


def percent(value):return '—' if value is None else f'{value*100:.2f}%'


def main():
    data=read_jsonl(ROOT/'data/main/FinanceBench.jsonl');a=read_jsonl(BEFORE/'predictions.jsonl');b=read_jsonl(AFTER/'predictions.jsonl')
    ids=[r['id'] for r in data]
    assert len(ids)==67 and [r['id'] for r in a]==ids and [r['id'] for r in b]==ids,'incomplete or reordered full run'
    lookup={r['id']:r for r in data}
    a=[{**r,'correct':correctness(lookup[r['id']],r['result'])} for r in a]
    b=[{**r,'correct':correctness(lookup[r['id']],r['result'])} for r in b]
    old,new=summarize(a,67),summarize(b,67)
    assert new['complete'] and not new['errors']
    assert new==json.loads((AFTER/'metrics.json').read_text(encoding='utf-8'))
    plan=json.loads((ROOT/'research/revised_full_run_plan.json').read_text(encoding='utf-8'))
    assert plan['source_hashes']==source_hashes(ROOT),'inference source changed during run'
    assert plan['dataset_sha256']==digest(ROOT/'data/main/FinanceBench.jsonl')
    assert plan['asset_lock_sha256']==digest(ROOT/'data/assets.lock.json')
    transitions=[]
    for before,after in zip(a,b):
        transitions.append({'id':after['id'],'before':category(before),'after':category(after),
            'before_status':before['result']['status'],'after_status':after['result']['status'],
            'before_reason':before['result'].get('reason'),'after_reason':after['result'].get('reason'),
            'candidate_unchanged':before['raw_answer']==after['raw_answer'],
            'retrieval_plan_unchanged':before['retrieval_plan']==after['retrieval_plan'],
            'retrieved_chunk_ids_unchanged':selected_chunks(before)==selected_chunks(after)})
    assert all(t['candidate_unchanged'] and t['retrieval_plan_unchanged'] and t['retrieved_chunk_ids_unchanged'] for t in transitions),'candidate or evidence changed; report comparability explicitly'
    proofs=[]
    for row in b:
        if row['result']['status'] not in {'VERIFIED','VIOLATED'}:continue
        path=AFTER/'smt'/(row['id']+'.smt2');s=z3.Solver();s.set(timeout=5000);s.from_string(path.read_text(encoding='utf-8'))
        got=str(s.check());expected='sat' if row['result']['status']=='VERIFIED' else 'unsat'
        assert got==expected,(row['id'],got,expected)
        proofs.append({'id':row['id'],'sha256':digest(path),'expected':expected,'replayed':got})
    counts=Counter((t['before'],t['after']) for t in transitions)
    gains={
        'new_true_accepts':[t['id'] for t in transitions if t['before']!='TA' and t['after']=='TA'],
        'lost_true_accepts':[t['id'] for t in transitions if t['before']=='TA' and t['after']!='TA'],
        'new_true_rejects':[t['id'] for t in transitions if t['before']!='TR' and t['after']=='TR'],
        'new_false_accepts':[t['id'] for t in transitions if t['before']!='FA' and t['after']=='FA'],
        'new_false_rejects':[t['id'] for t in transitions if t['before']!='FR' and t['after']=='FR'],
        'false_accepts_correctly_rejected':[t['id'] for t in transitions if t['before']=='FA' and t['after']=='TR'],
        'false_accepts_now_abstained':[t['id'] for t in transitions if t['before']=='FA' and t['after']=='Abs'],
    }
    errors=[]
    for r in b:
        if category(r) not in {'FA','FR'}:continue
        result=r['result'];q=lookup[r['id']]
        errors.append({'id':r['id'],'category':category(r),'question':q['question'],'reference':q['gold'],
                       'claimed_value':result.get('claimed_value'),'claimed_unit':result.get('claimed_unit'),
                       'formula_authority':result.get('audit',{}).get('formula_authority'),
                       'bindings':result.get('audit',{}).get('bindings')})
    reasons=Counter(r['result'].get('reason','').split(':')[0] for r in b if r['result']['status']=='ABSTAIN')
    out=AFTER.parent.parent
    audit={'completed_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'FinanceBench 67 only; requested GPT-5.6 Sol',
        'before':old,'after':new,'all_67_candidates_and_retrieved_evidence_identical':True,
        'source_and_input_hashes_unchanged':True,'transitions':dict((x+' -> '+y,n) for (x,y),n in sorted(counts.items())),
        'changes':gains,'abstention_reason_groups':dict(reasons),'SMT_proofs_replayed':len(proofs),'all_SMT_replays_matched':True,
        'before_source_sha256':digest(BEFORE/'predictions.jsonl'),'after_source_sha256':digest(AFTER/'predictions.jsonl'),
        'paper_source':'User VeriFin v3 PDF page 8 Table 4, FinanceBench n=67',
        'paper_snapshot_equivalence_claimed':False}
    write_json(out/'comparison.json',audit);write_json(out/'transitions.json',transitions)
    write_json(out/'error_cases.json',errors);write_json(out/'smt_replay.json',proofs)
    lines=['# FinanceBench 67 题：修改前、修改后与论文对比','',
        '仅运行用户指定的 VeriFin 主模型和 GPT-5.6 Sol 接口。完整 67 题、候选答案、检索计划与检索片段全部一致；未改金标、未放宽容差、未修复或重新采样答案。修改前后统一使用当前评测器。','',
        '| 指标 | 修改前 GPT-5.6 Sol | 修改后 GPT-5.6 Sol | 论文 GPT-5.5 |',
        '|---|---:|---:|---:|']
    for label,key,paper in [('正确接受 TA','TA',34),('误接受 FA','FA',0),('正确拒绝 TR','TR',None),('误拒绝 FR','FR',6),('弃答','Abs',20),('正确性未决','unresolved_decided',None),('运行错误','errors',None),('遗漏','missing',None)]:
        lines.append(f'| {label} | {old[key]} | {new[key]} | {paper if paper is not None else "表中未单列"} |')
    for label,key,paper in [('接受精度','precision',100),('验证决策准确率','accuracy',86.7),('覆盖率','coverage',70.1)]:
        lines.append(f'| {label} | {percent(old[key])} | {percent(new[key])} | {paper:.1f}% |')
    lines+=['','决策准确率只统计正确性已确定的接受/拒绝决策，不是全部问题的问答准确率；未决判定仍计入覆盖率。',
        '',f'相对修改前：接受精度提高 {(new["precision"]-old["precision"])*100:.2f} 个百分点，决策准确率提高 {(new["accuracy"]-old["accuracy"])*100:.2f} 个百分点，覆盖率提高 {(new["coverage"]-old["coverage"])*100:.2f} 个百分点。',
        '',f'相对论文 GPT-5.5 行：接受精度低 {100-new["precision"]*100:.2f} 个百分点，决策准确率约低 {86.7-new["accuracy"]*100:.2f} 个百分点，覆盖率约低 {70.1-new["coverage"]*100:.2f} 个百分点（论文表中数值已四舍五入）。本次未复现论文的零误接受结论。',
        '', '## 同候选逐题变化','']
    for label,key in [('新增正确接受','new_true_accepts'),('丢失原有正确接受','lost_true_accepts'),('新增正确拒绝','new_true_rejects'),('新增误接受','new_false_accepts'),('新增误拒绝','new_false_rejects'),('原误接受改为正确拒绝','false_accepts_correctly_rejected'),('原误接受改为弃答','false_accepts_now_abstained')]:
        lines.append(f'- {label}：{len(gains[key])} 条'+('；'+', '.join(gains[key]) if gains[key] else '。'))
    lines+=['','## 论文 Table 4 的全部 FinanceBench 行','',
        '| 骨干 | TA | FA | FR | Abs | 接受精度 | 决策准确率 | 覆盖率 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for model,ta,fa,fr,abs_,p,acc,cov in PAPER:lines.append(f'| 论文 {model} | {ta} | {fa} | {fr} | {abs_} | {p:.1f}% | {acc:.1f}% | {cov:.1f}% |')
    for label,m in [('修改前 GPT-5.6 Sol',old),('修改后 GPT-5.6 Sol',new)]:
        lines.append('| '+' | '.join([label,*[str(m[k]) for k in ['TA','FA','FR','Abs']],*[percent(m[k]) for k in ['precision','accuracy','coverage']]])+' |')
    lines+=['','## 修改后指标的不确定性','']
    for label,key in [('接受精度','precision'),('决策准确率','accuracy'),('覆盖率','coverage')]:
        lo,hi=new[key+'_ci95'];lines.append(f'- {label}的 95% Clopper–Pearson 区间：[{lo*100:.2f}%, {hi*100:.2f}%]。')
    lines+=['','## 剩余问题与可比性','',
        f'修改后仍有 {new["FA"]} 条误接受、{new["FR"]} 条误拒绝、{new["Abs"]} 条弃答。误接受/误拒绝的原始数值与来源绑定见 `error_cases.json`；逐题转移见 `transitions.json`。',
        '', '本次保留的 5 条 FA 均为原有金额舍入差异：1615.9 对 1616.00、381.603 对 382.00、3215.4 对 3215.00、302.578 对 303.00、5466.312 对 5466.00，单位均为百万美元。没有修改金标、放宽正式计分容差或把这些案例改记为正确。原 Pepsi 0 对 411 百万美元的概念误绑已改为正确拒绝。',
        '', '退步案例为 financebench_id_03031（Lockheed Martin 净营运资本）：题目用 “total current assets less total current liabilities” 定义减法，当前显式定义解析器未识别 less，按严格保护规则弃答，损失了 1 条原有正确接受。该限制在本次冻结全量中原样保留，没有边跑边改代码。',
        '', '正确性未决从 2 条增至 3 条。新增 financebench_id_00724 的参考目标为地区名称，当前数值验证不能据此判断地域选择正确性；该项计入覆盖率，不计作正确拒绝或计入决策准确率。覆盖率提升不全等同于新增已知正确决策。',
        '', '弃答首个失败原因：'+json.dumps(dict(reasons),ensure_ascii=False),
        '',f'本次 {len(proofs)} 份接受/拒绝 SMT 证明已独立重放，SAT/UNSAT 全部一致。该检查确认已编码算术约束的求解结果，业务语义仍按数据标签单独评测。',
        '', '论文对照依据用户附件第 8 页 Table 4，原表图像为 `research/paper-main-table.png`。本次骨干由用户指定，且公开资产与检索实现存在已记录差异；与论文为跨配置的描述性比较。修改前后则使用同一候选池和相同文档证据，可以直接检查代码变更导致的判定变化。',
        '', '没有运行 XBRLFiling、其他骨干、基线、repair、消融或训练。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'before':old,'after':new,'changes':gains,'proofs_replayed':len(proofs)},ensure_ascii=True,indent=2))
    print(str(out/'comparison.md'))


if __name__=='__main__':main()
