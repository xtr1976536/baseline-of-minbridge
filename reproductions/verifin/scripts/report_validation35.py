"""Audit a predeclared 35-question run with two separately named scoring rules."""
from pathlib import Path
import json
from collections import Counter
import z3
from vf_repro.common import read_jsonl,write_json,digest
from vf_repro.runner import source_hashes,asset_hashes,check
from vf_repro.scoring import correctness,summarize


def main():
    root=Path(__file__).resolve().parent.parent
    cfg_path=root/'configs/validation35-v1.json';cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
    manifest=json.loads((root/cfg['validation_manifest']).read_text(encoding='utf-8'))
    plan=json.loads((root/'research/validation35_run_plan.json').read_text(encoding='utf-8'))
    assert digest(cfg_path)==plan['config_sha256'] and source_hashes(root)==plan['source_hashes']
    assert digest(root/cfg['validation_manifest'])==plan['manifest_sha256']
    assert digest(root/cfg['validation_inputs_lock'])==plan['extra_inputs_lock_sha256']
    assert digest(root/'research/validation35-tests.xml')==plan['tests_xml_sha256']
    assert digest(root/'research/validation35_preflight_retrieval.json')==plan['preflight_retrieval_sha256']
    assert asset_hashes(root,['FinanceBench'])==plan['asset_hashes']
    assert check(root,cfg)['ready']
    lock=json.loads((root/cfg['validation_inputs_lock']).read_text(encoding='utf-8'))
    assert all(digest(root/k)==v for k,v in lock['files'].items()) and not any((root/k).exists() for k in lock['absent'])
    out=root/cfg['output_dir'];base=out/'GPT-5.6-Sol/FinanceBench'
    rows=read_jsonl(base/'predictions.jsonl');ids=manifest['ids'];assert len(ids)==35 and [r['id'] for r in rows]==ids
    data={r['id']:r for r in read_jsonl(root/'data/main/FinanceBench.jsonl')}
    assert digest(root/'data/main/FinanceBench.jsonl')==manifest['dataset_sha256']
    assert digest(root/manifest['baseline_source'])==plan['baseline_predictions_sha256']
    old={r['id']:r for r in read_jsonl(root/manifest['baseline_source'])}
    primary=cfg['evaluation']['primary_scoring_policy'];policies=[primary,'legacy_display_precision']
    comparison={}
    for policy in policies:
        before=summarize([{**old[i],'correct':correctness(data[i],old[i]['result'],policy=policy)} for i in ids],35)
        after=summarize([{**r,'correct':correctness(data[r['id']],r['result'],policy=policy)} for r in rows],35)
        comparison[policy]={'before':before,'after':after}
    after=comparison[primary]['after'];assert after==json.loads((base/'metrics.json').read_text(encoding='utf-8'))
    legacy=comparison['legacy_display_precision']['after'];assert legacy==json.loads((base/'metrics_legacy_display_precision.json').read_text(encoding='utf-8'))
    for r in rows:
        assert r['correct']==correctness(data[r['id']],r['result'],policy=primary)
        assert r['correct_legacy_display_precision']==correctness(data[r['id']],r['result'])
    proofs=[]
    for r in rows:
        if r['result']['status'] not in {'VERIFIED','VIOLATED'}:continue
        p=base/'smt'/(r['id']+'.smt2');solver=z3.Solver();solver.set(timeout=5000)
        solver.from_string(p.read_text(encoding='utf-8'));got=str(solver.check())
        assert got==('sat' if r['result']['status']=='VERIFIED' else 'unsat')
        proofs.append({'id':r['id'],'sha256':digest(p),'replayed':got})
    gate={k:after[k] is not None and after[k]>=v for k,v in manifest['targets'].items()}
    gate['complete_without_errors']=after['complete']
    legacy_gate={k:legacy[k] is not None and legacy[k]>=v for k,v in manifest['targets'].items()}
    legacy_gate['complete_without_errors']=legacy['complete']
    disagreements=[];errors=[];abstentions=[]
    for r in rows:
        sid=r['id'];s=r['result'];a=s.get('audit',{})
        item={'id':sid,'question':data[sid]['question'],'reference':data[sid]['gold'],'raw_answer':r['raw_answer'],
            'status':s['status'],'claimed_value':s.get('claimed_value'),'unit':s.get('claimed_unit'),'expected':s.get('expected'),
            'primary_correct':r['correct'],'legacy_correct':r['correct_legacy_display_precision'],
            'reason':s.get('reason'),'formula_authority':a.get('formula_authority'),'bindings':a.get('bindings'),
            'tolerance':a.get('tolerance'),'tolerance_source':a.get('tolerance_source')}
        if r['correct']!=r['correct_legacy_display_precision']:disagreements.append(item)
        if (s['status']=='VERIFIED' and r['correct'] is False) or (s['status']=='VIOLATED' and r['correct'] is True):errors.append(item)
        if s['status']=='ABSTAIN':abstentions.append(item)
    audit={'N':35,'all_ids_unchanged':True,'sources_config_assets_unchanged':True,'gold_labels_unchanged':True,
        'primary_scoring_policy':primary,'local_rounding_rule_not_author_official_numeric_threshold':True,
        'comparison':comparison,'targets':manifest['targets'],'gate':gate,'all_primary_gates_met':all(gate.values()),
        'legacy_gate':legacy_gate,'all_legacy_gates_met':all(legacy_gate.values()),
        'scoring_disagreements':len(disagreements),'proofs_replayed':len(proofs),'all_proofs_matched':True,
        'new_full_67_started':False,'other_datasets_run':False,
        'abstention_reasons':dict(Counter(x['reason'].split(':')[0] for x in abstentions)),
        'source_hashes':source_hashes(root)}
    write_json(out/'validation.json',audit);write_json(out/'scoring_disagreements.json',disagreements)
    write_json(out/'error_cases.json',errors);write_json(out/'abstentions.json',abstentions);write_json(out/'smt_replay.json',proofs)
    before=comparison[primary]['before'];old_legacy=comparison['legacy_display_precision']['before']
    lines=['# 固定 35 题验证','',f'三项数值门槛全部通过（当前预先冻结的主评分口径）：**{all(gate.values())}**。',
        '', '同一旧哈希种子选取前 35 个 ID，在本轮修改和推理前固定；未换题、删失败题或改金标。仅 FinanceBench、同一 GPT-5.6 Sol 接口。',
        '', '## 主评分与模型改进','',
        '原始 FinanceBench §4.1 人工评审允许单位换算及微小舍入，未提供统一数值阈值。本轮先声明本地规则：明确题目精度优先；否则货币标签去掉末尾格式补零后取半 ULP；零值精确匹配；百分比、比率等继续按其参考精度。它是本地操作化，不声称作者发布过该阈值。验证器的事实、公式和数值容差不读取金标，评分只在验证结束后执行。',
        '', '| 指标 | 修改前同 35 题（同一评分规则） | 本轮 35 题 | 论文 GPT-5.5 数值目标 |',
        '|---|---:|---:|---:|']
    for label,k in [('接受精度','precision'),('决策准确率','accuracy'),('覆盖率','coverage')]:
        fmt=lambda v:'—' if v is None else f'{100*v:.2f}%'
        lines.append(f'| {label} | {fmt(before[k])} | {fmt(after[k])} | {fmt(manifest["targets"][k])} |')
    for label,k in [('TA','TA'),('FA','FA'),('TR','TR'),('FR','FR'),('弃答','Abs'),('正确性未决','unresolved_decided'),('错误','errors'),('遗漏','missing')]:
        lines.append(f'| {label} | {before[k]} | {after[k]} | — |')
    lines+=['','## 旧严格口径（完整保留）','','| 指标 | 修改前同 35 题 | 本轮 35 题 |','|---|---:|---:|']
    for label,k in [('接受精度','precision'),('决策准确率','accuracy'),('覆盖率','coverage')]:
        lines.append(f'| {label} | {100*old_legacy[k]:.2f}% | {100*legacy[k]:.2f}% |')
    lines+=['',f'两种评分对 {len(disagreements)} 条结果判断不同，逐题保存在 `scoring_disagreements.json`。评分口径造成的变化不计为模型改进。',
        '',f'旧严格口径三项门槛全部通过：**{all(legacy_gate.values())}**。',
        '', '## 验证与边界','',f'{len(proofs)} 份 SMT 重放一致；证明只确认给定约束的算术一致性。',
        '', '这是修改后 35 题开发验证，骨干和规模与论文 67 题/GPT-5.5 不同；不声称恢复了作者全部未公开资产或完成全量复现。没有新跑 67 题、其他数据集、其他骨干、baseline 或 repair。',
        '', '[VeriFin Table 4](https://arxiv.org/html/2608.10213v3)；[FinanceBench §4.1](https://arxiv.org/pdf/2311.11944)。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='source_hashes'},ensure_ascii=True,indent=2))


if __name__=='__main__':main()
