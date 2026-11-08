"""Audit the fixed 50-question validation and apply its predeclared strict gate."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json
import argparse
import z3
from vf_repro.common import read_jsonl,write_json,digest,fingerprint
from vf_repro.runner import source_hashes
from vf_repro.scoring import correctness,summarize


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/coverage50.json')
    parser.add_argument('--plan',default='research/coverage50_run_plan.json')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    cfg=json.loads((root/args.config).read_text(encoding='utf-8'))
    manifest=json.loads((root/cfg['validation_manifest']).read_text(encoding='utf-8'))
    plan=json.loads((root/args.plan).read_text(encoding='utf-8'))
    lock=json.loads((root/cfg['validation_inputs_lock']).read_text(encoding='utf-8'))
    out=root/cfg['output_dir'];base=out/'GPT-5.6-Sol/FinanceBench'
    rows=read_jsonl(base/'predictions.jsonl');ids=manifest['ids'];n=len(ids)
    assert n>=50 and n<67 and [r['id'] for r in rows]==ids
    assert digest(root/args.config)==plan['config_sha256']
    assert digest(root/cfg['validation_inputs_lock'])==plan['extra_inputs_lock_sha256']
    assert digest(root/'data/main/FinanceBench.jsonl')==manifest['dataset_sha256']
    assert source_hashes(root)==plan['source_hashes']
    if plan.get('validation_script_sha256'):
        assert digest(root/'scripts/reverify_coverage50.py')==plan['validation_script_sha256']
    assert digest(root/cfg['validation_manifest'])==plan['manifest_sha256']
    assert all(digest(root/k)==v for k,v in lock['files'].items())
    assert not any((root/k).exists() for k in lock['absent'])
    data={r['id']:r for r in read_jsonl(root/'data/main/FinanceBench.jsonl')}
    assert all(r['correct']==correctness(data[r['id']],r['result']) for r in rows)
    old={r['id']:r for r in read_jsonl(root/manifest['baseline_source'])}
    before=summarize([{**old[i],'correct':correctness(data[i],old[i]['result'])} for i in ids],n)
    after=summarize(rows,n);assert after==json.loads((base/'metrics.json').read_text(encoding='utf-8'))
    gate={key:after[key] is not None and after[key]>=target for key,target in manifest['targets'].items() if key in {'precision','accuracy','coverage'}}
    gate['complete_without_errors']=after['complete'];success=all(gate.values())
    proofs=[]
    for r in rows:
        if r['result']['status'] not in {'VERIFIED','VIOLATED'}:continue
        p=base/'smt'/(r['id']+'.smt2');solver=z3.Solver();solver.set(timeout=5000);solver.from_string(p.read_text(encoding='utf-8'))
        got=str(solver.check());expected='sat' if r['result']['status']=='VERIFIED' else 'unsat';assert got==expected,(r['id'],got)
        proofs.append({'id':r['id'],'sha256':digest(p),'replayed':got})
    errors=[]
    for r in rows:
        if (r['result']['status']=='VERIFIED' and r['correct'] is False) or (r['result']['status']=='VIOLATED' and r['correct'] is True):
            a=r['result'];errors.append({'id':r['id'],'question':data[r['id']]['question'],'reference':data[r['id']]['gold'],
                'claim':a.get('claimed_value'),'unit':a.get('claimed_unit'),'status':a['status'],
                'expected':a.get('expected'),'authority':a.get('audit',{}).get('formula_authority'),
                'raw_answer':r['raw_answer'],'tolerance':a.get('audit',{}).get('tolerance'),
                'tolerance_source':a.get('audit',{}).get('tolerance_source'),
                'bindings':a.get('audit',{}).get('bindings')})
    reasons=dict(Counter(r['result'].get('reason','').split(':')[0] for r in rows if r['result']['status']=='ABSTAIN'))
    audit={'time_utc':datetime.now(timezone.utc).isoformat(),'N':n,'selection':manifest['selection_rule'],'seed':manifest['seed'],
        'before':before,'after':after,'targets':manifest['targets'],'gate':gate,'modification_success':success,
        'full_67_started':False,'legacy_strict_scoring_unchanged':True,'new_evidence_and_candidates':not bool(cfg.get('frozen_candidate_source')),
        'source_and_extra_inputs_unchanged':True,'abstention_reasons':reasons,'proofs_replayed':len(proofs),
        'all_proofs_matched':True,'source_hashes':source_hashes(root)}
    preceding=None
    if plan.get('preceding_validation'):
        preceding=json.loads((root/plan['preceding_validation']).read_text(encoding='utf-8'))
        assert preceding['N']==n and preceding['seed']==manifest['seed']
        prior_base=(root/plan['preceding_validation']).parent/'GPT-5.6-Sol/FinanceBench/predictions.jsonl'
        assert digest(prior_base)==plan['preceding_predictions_sha256']
        assert [r['id'] for r in read_jsonl(prior_base)]==ids
        audit['preceding_validation']={'path':plan['preceding_validation'],'metrics':preceding['after'],
            'modification_success':preceding['modification_success'],'preserved_predictions_sha256':digest(prior_base)}
    if cfg.get('frozen_candidate_source'):
        from vf_repro.retrieval import chunks_from_pages
        prior={r['id']:r for r in read_jsonl(root/cfg['frozen_candidate_source'])}
        assert digest(root/cfg['frozen_candidate_source'])==cfg['frozen_candidate_sha256']
        for r in rows:
            sid=r['id'];assert r['raw_answer']==prior[sid]['raw_answer']
            assert r['retrieval']==prior[sid]['retrieval']
            c=cfg['retrieval'];doc=data[sid]['doc_name']
            pages=json.loads((root/'data/corpus'/(doc+'.json')).read_text(encoding='utf-8'))['pages']
            chunks=chunks_from_pages(doc,pages,words=c['chunk_words'],overlap=c['chunk_overlap_words'],table_aware=c.get('table_aware',False))
            by_id={x.chunk_id:x for x in chunks};chosen=prior[sid]['retrieval'][0]['selection']['ids']
            assert r['frozen_input']['evidence_sha256']==fingerprint('\n\n'.join(by_id[k].text for k in chosen))
            assert r['frozen_input']['candidate_sha256']==fingerprint(r['raw_answer'])
        audit['all_50_candidates_and_evidence_identical_to_preceding']=True
    write_json(out/'validation.json',audit);write_json(out/'error_cases.json',errors);write_json(out/'smt_replay.json',proofs)
    input_note=('本轮完全复用上一轮 50 个候选与实际选中证据，只重验验证器；相对上一轮是同候选比较，相对修改前历史结果仍是同问题、不同候选的版本比较。' if cfg.get('frozen_candidate_source') else
        '本轮改动检索，故候选也按新证据生成一次，前后是同问题的端到端比较，不是同候选的纯验证器比较。')
    lines=['# 固定 50 题覆盖率验证','',
        '50 个 ID 在修改前用固定 SHA-256 排序规则选定；未按结果换题或排除失败题。'+input_note,
        '', '| 指标 | 修改前同 50 题 | 本次 50 题 | 论文 GPT-5.5 目标 | 达标 |',
        '|---|---:|---:|---:|---|']
    for label,key,target in [('接受精度','precision',1.0),('决策准确率','accuracy',.867),('覆盖率','coverage',.701)]:
        values=['—' if m[key] is None else f'{m[key]*100:.2f}%' for m in [before,after]]
        lines.append('| '+' | '.join([label,*values,f'{target*100:.1f}%',str(gate[key])])+' |')
    for label,key in [('TA','TA'),('FA','FA'),('TR','TR'),('FR','FR'),('弃答','Abs'),('正确性未决','unresolved_decided'),('运行错误','errors'),('遗漏','missing')]:
        lines.append(f'| {label} | {before[key]} | {after[key]} | — | — |')
    if preceding:
        m=preceding['after']
        change_note=('本轮修复跨年度比例的叶子角色展开，以及将操作数小计误作整个比例目标的问题；候选、证据、事实、计分和模型不变。' if cfg.get('frozen_candidate_source') else
            '本轮只新增操作数精确表行的有界保留约束，原始事实、公式授权、计分、样本和模型不变。')
        lines+=['',f'上一轮相同 50 题结果完整保留：接受精度 {m["precision"]*100:.2f}%、决策准确率 {m["accuracy"]*100:.2f}%、覆盖率 {m["coverage"]*100:.2f}%，修改成功 = {preceding["modification_success"]}。'+change_note]
    lines+=['',f'按预先声明的严格口径：**修改成功 = {success}**。只在全部指标达标且 50 题完整、无运行错误时判为成功。',
        '', '## 剩余问题','',json.dumps(reasons,ensure_ascii=False),
        '', '误接受/误拒绝案例完整保存于 `error_cases.json`；未修改金标或用较宽容差覆盖旧严格结果。',
        '', f'{len(proofs)} 份接受/拒绝 SMT 证明重放一致；证明只确认给定约束的算术一致性。',
        '', '原始 FinanceBench §4.1 采用人工标注并允许微小舍入误差，但未公开统一数值阈值。VeriFin §4.2 使用各数据集评分策略。因此原有严格“标签小数位”计分与论文人工口径存在未解决的可比性差异；本报告保留严格结果，不据此改记 100%。',
        '', '- FinanceBench: https://arxiv.org/pdf/2311.11944',
        '- VeriFin: https://arxiv.org/html/2608.10213v3',
        '', '没有启动 67 题全量、其他数据集、其他骨干、baseline、repair 或训练。']
    if errors:
        lines+=['','## 严格误判明细','','| ID | 判定 | 候选 | 参考答案 | 单位 | 验证容差来源 |',
                '|---|---|---:|---|---|---|']
        for e in errors:
            lines.append('| '+' | '.join([e['id'],e['status'],str(e['claim']),str(e['reference']['answer']),
                str(e['unit']),str(e['tolerance'])+' / '+str(e['tolerance_source'])])+' |')
        lines+=['','上述金额差异保留为严格误接受。对于问题未指定输出精度的派生比例，本地旧有两位小数假设仍使用 τ=0.005；它不是论文公开的统一精度规则。本轮未按个别案例改宽容差，相关误拒绝仍保留。',
                '', '已核对的检索遗漏、多步公式修正、各版计数及剩余问题详见 `../../docs/COVERAGE50_FIXES.md`。']
    (out/'coverage_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='source_hashes'},ensure_ascii=True,indent=2))


if __name__=='__main__':main()
