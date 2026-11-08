# 固定 50 题覆盖率验证

50 个 ID 在修改前用固定 SHA-256 排序规则选定；未按结果换题或排除失败题。本轮完全复用上一轮 50 个候选与实际选中证据，只重验验证器；相对上一轮是同候选比较，相对修改前历史结果仍是同问题、不同候选的版本比较。

| 指标 | 修改前同 50 题 | 本次 50 题 | 论文 GPT-5.5 目标 | 达标 |
|---|---:|---:|---:|---|
| 接受精度 | 78.95% | 77.78% | 100.0% | False |
| 决策准确率 | 79.17% | 76.67% | 86.7% | False |
| 覆盖率 | 52.00% | 62.00% | 70.1% | False |
| TA | 15 | 21 | — | — |
| FA | 4 | 6 | — | — |
| TR | 4 | 2 | — | — |
| FR | 1 | 1 | — | — |
| 弃答 | 24 | 19 | — | — |
| 正确性未决 | 2 | 1 | — | — |
| 运行错误 | 0 | 0 | — | — |
| 遗漏 | 0 | 0 | — | — |

上一轮相同 50 题结果完整保留：接受精度 76.92%、决策准确率 75.86%、覆盖率 60.00%，修改成功 = False。本轮修复跨年度比例的叶子角色展开，以及将操作数小计误作整个比例目标的问题；候选、证据、事实、计分和模型不变。

按预先声明的严格口径：**修改成功 = False**。只在全部指标达标且 50 题完整、无运行错误时判为成功。

## 剩余问题

{"missing_or_ambiguous_filing_fact": 4, "no_usable_numeric_claim": 1, "verification_plan_has_no_roles": 7, "formula_authority_not_established": 3, "ambiguous_or_unresolved_registry_formula": 2, "candidate_generation_produced_no_usable_answer": 1, "missing_reporting_period": 1}

误接受/误拒绝案例完整保存于 `error_cases.json`；未修改金标或用较宽容差覆盖旧严格结果。

31 份接受/拒绝 SMT 证明重放一致；证明只确认给定约束的算术一致性。

原始 FinanceBench §4.1 采用人工标注并允许微小舍入误差，但未公开统一数值阈值。VeriFin §4.2 使用各数据集评分策略。因此原有严格“标签小数位”计分与论文人工口径存在未解决的可比性差异；本报告保留严格结果，不据此改记 100%。

- FinanceBench: https://arxiv.org/pdf/2311.11944
- VeriFin: https://arxiv.org/html/2608.10213v3

没有启动 67 题全量、其他数据集、其他骨干、baseline、repair 或训练。

## 严格误判明细

| ID | 判定 | 候选 | 参考答案 | 单位 | 验证容差来源 |
|---|---|---:|---|---|---|
| financebench_id_04672 | VERIFIED | 8.738 | $8.70 | USD billions | 0.0005000000 / filing_fact_decimals |
| financebench_id_03882 | VERIFIED | 1615.9 | $1616.00 | USD millions | 0.0500000 / filing_fact_decimals |
| financebench_id_05718 | VERIFIED | 0.389 | $0.40 | USD billions | 0.0005000000 / filing_fact_decimals |
| financebench_id_07661 | VERIFIED | 381.603 | $382.00 | USD millions | 0.0005 / filing_display_scale |
| financebench_id_04854 | VERIFIED | 3215.4 | $3215.00 | USD millions | 0.5 / filing_display_scale |
| financebench_id_03282 | VERIFIED | 5466.312 | $5466.00 | USD millions | 0.0005 / filing_display_scale |
| financebench_id_04481 | VIOLATED | 16.5 | 16.5% | percent | .005 / reproduction_assumption_derived_ratio_two_decimals |

上述金额差异保留为严格误接受。对于问题未指定输出精度的派生比例，本地旧有两位小数假设仍使用 τ=0.005；它不是论文公开的统一精度规则。本轮未按个别案例改宽容差，相关误拒绝仍保留。

已核对的检索遗漏、多步公式修正、各版计数及剩余问题详见 `../../docs/COVERAGE50_FIXES.md`。
