"""Audit the user-authorized full 67-question continuation without changing scores."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from fractions import Fraction
from decimal import Decimal,localcontext
import ast
import json
import z3
from vf_repro.common import read_jsonl,write_json,write_jsonl,digest,fingerprint
from vf_repro.runner import source_hashes,asset_hashes,check
from vf_repro.scoring import correctness,summarize
from vf_repro.grounding import conversion
from audit_validation35_arithmetic import calculate


def percent(value):return '—' if value is None else f'{100*value:.2f}%'


def main():
    root=Path(__file__).resolve().parent.parent
    cfg_path=root/'configs/financebench-full-post35.json';cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
    plan=json.loads((root/'research/financebench_full_post35_run_plan.json').read_text(encoding='utf-8'))
    out=root/cfg['output_dir'];base=out/'GPT-5.6-Sol/FinanceBench'
    assert plan['user_authorized_full_67'] and cfg['datasets']==['FinanceBench']
    assert digest(cfg_path)==plan['config_sha256'] and source_hashes(root)==plan['source_hashes']
    assert digest(root/'data/assets.lock.json')==plan['asset_lock_sha256']
    assert asset_hashes(root,['FinanceBench'])==plan['asset_hashes'] and check(root,cfg)['ready']
    assert digest(root/cfg['full_inputs_lock'])==plan['extra_inputs_lock_sha256']==cfg['full_inputs_lock_sha256']
    lock=json.loads((root/cfg['full_inputs_lock']).read_text(encoding='utf-8'))
    assert all(digest(root/k)==v for k,v in lock['files'].items())
    assert not any((root/k).exists() for k in lock['absent'])
    assert digest(root/'data/main/FinanceBench.jsonl')==plan['dataset_sha256']
    data=read_jsonl(root/'data/main/FinanceBench.jsonl');ids=[r['id'] for r in data];lookup={r['id']:r for r in data}
    rows=read_jsonl(base/'predictions.jsonl');by_id={r['id']:r for r in rows}
    assert len(rows)==len(by_id)==len(ids)==67 and set(by_id)==set(ids) and ids==plan['ids']
    ordered=[by_id[i] for i in ids]
    assert digest(out/'seed_provenance.json')==plan['seed_provenance_sha256']
    seed=json.loads((out/'seed_provenance.json').read_text(encoding='utf-8'))
    assert digest(root/seed['source'])==seed['source_sha256']
    assert all(fingerprint(by_id[i])==h for i,h in seed['records'].items())
    assert all(digest(base/'smt'/(i+'.smt2'))==h for i,h in seed['copied_smt_sha256'].items())
    assert digest(root/'research/validation35-tests.xml')==plan['regression_test_xml_sha256']
    primary=cfg['evaluation']['primary_scoring_policy'];policies=[primary,'legacy_display_precision']
    baselines={}
    for rel,h in plan['baselines'].items():
        assert digest(root/rel)==h
        prior=read_jsonl(root/rel);assert len(prior)==67 and {r['id'] for r in prior}==set(ids)
        baselines[rel]=prior
    comparison={}
    for policy in policies:
        cells={rel:summarize([{**r,'correct':correctness(lookup[r['id']],r['result'],policy=policy)} for r in prior],67) for rel,prior in baselines.items()}
        cells['current_full67']=summarize([{**r,'correct':correctness(lookup[r['id']],r['result'],policy=policy)} for r in rows],67)
        comparison[policy]=cells
    current=comparison[primary]['current_full67'];legacy=comparison['legacy_display_precision']['current_full67']
    assert current==json.loads((base/'metrics.json').read_text(encoding='utf-8'))
    assert legacy==json.loads((base/'metrics_legacy_display_precision.json').read_text(encoding='utf-8'))
    for r in rows:
        assert r['correct']==correctness(lookup[r['id']],r['result'],policy=primary)
        assert r['correct_legacy_display_precision']==correctness(lookup[r['id']],r['result'])
    proofs=[];arithmetic=[];filings={}
    review=['# Full 67 candidate and arithmetic review','',
        '35 unchanged development records plus 32 records completed under identical code/settings. This checks arithmetic and fact identity; financial interpretation is reviewed separately.','',
        '| ID | Status | Reference | Initial answer |','|---|---|---|---|']
    for r in ordered:
        sid=r['id'];s=r['result'];d=lookup[sid]
        review.append('| '+' | '.join([sid,s['status'],str(d['gold']['answer']).replace('|','/'),r['raw_answer'].replace('|','/').replace('\n',' ')])+' |')
        if s['status'] not in {'VERIFIED','VIOLATED'}:continue
        smt=base/'smt'/(sid+'.smt2');solver=z3.Solver();solver.set(timeout=10000)
        solver.from_string(smt.read_text(encoding='utf-8'));got=str(solver.check())
        assert got==('sat' if s['status']=='VERIFIED' else 'unsat'),(sid,got)
        proofs.append({'id':sid,'sha256':digest(smt),'result':got})
        a=s['audit'];doc=d['doc_name']
        if doc not in filings:filings[doc]=json.loads((root/'data/filings'/(doc+'.json')).read_text(encoding='utf-8'))
        f=filings[doc]
        for b in a['bindings']:
            facts=[x for x in f['facts'] if x['id']==b['source_fact_id'] and x['concept']==b['concept'] and x['period']==b['period']]
            assert facts and all(Decimal(x['value'])*conversion(x['unit'],b['unit'])==Decimal(b['value']) for x in facts)
            assert b['source_sha256']==f['instance_sha256'] and b['accession']==f['accession']
        values={b['role']:Fraction(b['value']) for b in a['bindings']};claimed=Fraction(s['claimed_value']);tau=Fraction(a['tolerance'])
        tree=ast.parse(a['plan']['formula'],mode='eval').body
        if isinstance(tree,ast.Call) and tree.func.id in {'cagr','cagr_percent'}:
            end,start,n=[calculate(ast.unparse(x),values) for x in tree.args]
            assert start>0 and end>0 and n.denominator==1 and n>0
            factor=100 if tree.func.id=='cagr_percent' else 1
            lo=max(Fraction(0),1+(claimed-tau)/factor);hi=1+(claimed+tau)/factor;ratio=end/start
            accepted=hi>0 and lo**int(n)<=ratio<=hi**int(n)
            exact='('+str(ratio)+')^(1/'+str(n)+') with display factor '+str(factor)
            with localcontext() as ctx:
                ctx.prec=60;decimal=str(((Decimal(ratio.numerator)/Decimal(ratio.denominator))**(Decimal(1)/Decimal(n.numerator))-1)*factor)
        elif isinstance(tree,ast.Call) and tree.func.id=='coverage_ratio':
            numerator,denominator=[calculate(ast.unparse(x),values) for x in tree.args]
            expected=Fraction(0) if numerator<=0 else numerator/denominator
            accepted=abs(expected-claimed)<=tau;exact=str(expected)
            with localcontext() as ctx:
                ctx.prec=50;decimal=str(Decimal(expected.numerator)/Decimal(expected.denominator))
        else:
            expected=calculate(a['plan']['formula'],values);accepted=abs(expected-claimed)<=tau;exact=str(expected)
            with localcontext() as ctx:
                ctx.prec=50;decimal=str(Decimal(expected.numerator)/Decimal(expected.denominator))
        assert accepted==(s['status']=='VERIFIED'),sid
        arithmetic.append({'id':sid,'formula':a['plan']['formula'],'source_facts_replayed':len(a['bindings']),
            'expected_exact':exact,'expected_decimal':decimal,'claim':str(claimed),'tau':str(tau),'decision_matched':True})
    errors=[];disagreements=[];abstentions=[]
    for r in ordered:
        s=r['result'];a=s.get('audit',{});d=lookup[r['id']]
        item={'id':r['id'],'question':d['question'],'reference':d['gold'],'raw_answer':r['raw_answer'],'status':s['status'],
            'primary_correct':r['correct'],'legacy_correct':r['correct_legacy_display_precision'],'reason':s.get('reason'),
            'claimed_value':s.get('claimed_value'),'unit':s.get('claimed_unit'),'expected':s.get('expected'),
            'formula_authority':a.get('formula_authority'),'bindings':a.get('bindings'),'tolerance':a.get('tolerance'),'tolerance_source':a.get('tolerance_source')}
        if r['correct']!=r['correct_legacy_display_precision']:disagreements.append(item)
        if (s['status']=='VERIFIED' and r['correct'] is False) or (s['status']=='VIOLATED' and r['correct'] is True):errors.append(item)
        if s['status']=='ABSTAIN':abstentions.append(item)
    targets={'precision':1.,'accuracy':.867,'coverage':.701}
    unresolved=[{'id':r['id'],'status':r['result']['status']} for r in ordered
                if r['result']['status'] in {'VERIFIED','VIOLATED'} and r['correct'] is None]
    unresolved_accepted=sum(r['status']=='VERIFIED' for r in unresolved)
    conservative={}
    for policy,m in [(primary,current),('legacy_display_precision',legacy)]:
        accepted=m['TA']+m['FA']+unresolved_accepted
        decided=sum(m[k] for k in ['TA','FA','TR','FR','unresolved_decided'])
        conservative[policy]={'precision':m['TA']/accepted if accepted else None,
            'accuracy':(m['TA']+m['TR'])/decided if decided else None,'coverage':m['coverage'],
            'assumption':'Every unresolved decision counts as incorrect; original labels and scores remain unchanged.'}
    gates={p:{**{k:comparison[p]['current_full67'][k] is not None and comparison[p]['current_full67'][k]>=v for k,v in targets.items()},
        'complete_without_errors':comparison[p]['current_full67']['complete']} for p in policies}
    pending=set(plan['pending_ids']);new_rows=[r for r in rows if r['id'] in pending];assert len(new_rows)==32
    audit={'finished_at_utc':datetime.now(timezone.utc).isoformat(),'N':67,'completed':len(rows),'seeded_unchanged':35,'newly_completed':32,
        'source_code_unchanged_from_validation35':True,'same_inference_parameters':True,'same_scoring_policies':True,
        'gold_labels_and_ids_unchanged':True,'all_extra_inputs_and_absences_frozen':True,'primary_scoring_policy':primary,
        'local_primary_rounding_rule_not_author_official_threshold':True,'comparison':comparison,'targets':targets,'gates':gates,
        'all_primary_numeric_targets_met':all(gates[primary].values()),'all_legacy_numeric_targets_met':all(gates['legacy_display_precision'].values()),
        'new32_only':{p:summarize([{**r,'correct':correctness(lookup[r['id']],r['result'],policy=p)} for r in new_rows],32) for p in policies},
        'unresolved_decisions':unresolved,'conservative_unresolved_as_incorrect':conservative,
        'proofs_replayed':len(proofs),'independent_arithmetic_and_facts_replayed':len(arithmetic),'all_replays_matched':True,
        'scoring_disagreements':len(disagreements),'primary_error_cases':len(errors),
        'abstention_reasons':dict(Counter(x['reason'].split(':')[0] for x in abstentions)),
        'other_datasets_or_experiments_run':False,'paper_original_asset_or_backbone_equivalence_claimed':False,
        'journal_sha256':digest(base/'predictions.jsonl'),'source_hashes':source_hashes(root)}
    write_json(out/'validation.json',audit);write_json(out/'smt_replay.json',proofs)
    write_json(out/'independent_arithmetic.json',arithmetic);write_json(out/'error_cases.json',errors)
    write_json(out/'scoring_disagreements.json',disagreements);write_json(out/'abstentions.json',abstentions)
    write_jsonl(out/'predictions_dataset_order.jsonl',ordered)
    (out/'candidate_review.md').write_text('\n'.join(review)+'\n',encoding='utf-8')
    names=['runs/gpt56-sol-final/GPT-5.6-Sol/FinanceBench/predictions.jsonl',
           'runs/financebench-revised-v1/GPT-5.6-Sol/FinanceBench/predictions.jsonl']
    labels=['最初修改前67题','上一修正版67题','本次完整67题']
    lines=['# FinanceBench 全部 67 题：35 题版本的完整续跑','',
        '用户授权后，以已验证的相同代码、GPT-5.6 Sol 接口、检索与生成设置评估全部 67 个原始 ID。35 个已有记录逐字段原样复用，补跑另外 32 题；不是 67 题全新或独立的测试。未改代码、问题、金标、评分规则或删除失败题。',
        '', '## 运行前固定的主舍入口径','',
        '主规则为本地 financebench_currency_padding_v1：明确题目精度优先；否则货币参考值按去除末尾格式补零后的精度取半 ULP，零值精确匹配。它是对 FinanceBench 允许微小舍入原则的本地操作化，不是作者公布的官方数值阈值。修改前的结果也按相同规则统一计分，评分修正本身不计为模型收益。',
        '', '| 版本 | N | TA | FA | TR | FR | 弃答 | 未决 | 精度 | 决策准确率 | 覆盖率 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for label,key in zip(labels,[*names,'current_full67']):
        m=comparison[primary][key];lines.append('| '+' | '.join([label,'67',*[str(m[k]) for k in ['TA','FA','TR','FR','Abs','unresolved_decided']],*[percent(m[k]) for k in ['precision','accuracy','coverage']]])+' |')
    lines+=['| 论文 GPT-5.5 数值目标 | 67 | — | — | — | — | — | — | 100% | 86.7% | 70.1% |',
        '',f'主口径下全部数值门槛通过：**{all(gates[primary].values())}**。',
        '',f'自动正确性未决 {len(unresolved)} 条，覆盖率包含这些判定，常规决策准确率不包含；不能把该准确率解释为所有判定均正确。将所有未决判定均计作错误的保守敏感性结果：接受精度 {percent(conservative[primary]["precision"])}、决策准确率 {percent(conservative[primary]["accuracy"])}、覆盖率 {percent(conservative[primary]["coverage"])}。原始标签、常规计数和两套评分均未改变。',
        '', '## 原严格显示精度口径（完整保留）','','| 版本 | 精度 | 决策准确率 | 覆盖率 |','|---|---:|---:|---:|']
    for label,key in zip(labels,[*names,'current_full67']):
        m=comparison['legacy_display_precision'][key];lines.append('| '+' | '.join([label,*[percent(m[k]) for k in ['precision','accuracy','coverage']]])+' |')
    lines+=['',f'旧严格口径下全部数值门槛通过：**{all(gates["legacy_display_precision"].values())}**。两套口径对 {len(disagreements)} 条结果判断不同，详见 `scoring_disagreements.json`，未混用两种规则宣称达标。',
        '', '## 覆盖率与失败点','',
        f'35 条既有验证记录覆盖 29/35（82.86%），另外 32 条覆盖 {audit["new32_only"][primary]["TA"]+audit["new32_only"][primary]["FA"]+audit["new32_only"][primary]["TR"]+audit["new32_only"][primary]["FR"]+audit["new32_only"][primary]["unresolved_decided"]}/32（{percent(audit["new32_only"][primary]["coverage"])}）。后者不是独立留出集，不能把两组差异当作独立泛化实验。',
        '',f'完整覆盖率 {percent(current["coverage"])}，论文目标 70.1% 在 67 题上需要至少 47 条判定；本轮有 {len(proofs)} 条，仍差 {max(0,47-len(proofs))} 条。没有删弃答、追加抽题、重采样或事后改变规则来补足覆盖率。',
        '', '| 弃答原因 | 数量 |', '|---|---:|',
        *['| '+k+' | '+str(v)+' |' for k,v in audit['abstention_reasons'].items()],
        '', '沃尔玛 04784：接口返回了可读的 0.2 个百分点答案，但未返回提示要求的 JSON，因此被当前生成解析器记为弃答（不是接口空响应）。原接口响应保留在请求缓存，未重新请求或事后填入预测。沃尔玛 06741：缺少/歧义绑定 FY2018 D&A，保持弃答；候选 6.3% 与参考 6.2% 也不同，不能直接接受它来补足覆盖。',
        '', 'Corning 01346：候选税率变化为 2.7 个百分点，两个绑定已是 percent 单位（20.2、22.9），公式仍乘 100，存在重复百分比换算的问题。该题参考包含两个税率，自动标量评分保持未决；数学证明重放一致不能消除这一语义错误。该题未改标签或判定，也没有藏入正确拒绝。详见 `response_review.json`。',
        '', '## 完整性与可比性','',f'全部 67 个 ID 完整，运行错误 {current["errors"]}、遗漏 {current["missing"]}。{len(proofs)} 份 SMT 重放一致，另有 {len(arithmetic)} 个判定的原事实身份、期间、单位换算和独立算术检查一致。SMT/算术一致性不代替金融语义审查。',
        '', '35 条复用记录及其 SMT 哈希全部与原验证一致。原追加日志按“35 条复用＋32 条补跑”记录；另提供按原数据集顺序排列的 `predictions_dataset_order.jsonl`，没有修改运行日志。',
        '', '比较为不同代码版本、不同候选池的端到端描述，不能解释为相同候选的纯验证器收益。骨干为用户指定 GPT-5.6 Sol，论文参考行为 GPT-5.5；公开资产、检索 checkpoint 和评分细则的差异仍保留，不声称完全恢复作者原始设置。仅运行 FinanceBench 主模型，没有运行其他数据集、骨干、baseline、repair 或训练。',
        '', '[VeriFin Table 4](https://arxiv.org/html/2608.10213v3)；[FinanceBench §4.1](https://arxiv.org/pdf/2311.11944)。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='source_hashes'},ensure_ascii=True,indent=2))


if __name__=='__main__':main()
