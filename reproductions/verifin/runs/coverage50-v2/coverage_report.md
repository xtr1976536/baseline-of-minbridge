# 固定 50 题覆盖率验证

50 个 ID 在修改前用固定 SHA-256 排序规则选定；未按结果换题或排除失败题。本轮改动检索，故候选也按新证据生成一次，前后是同问题的端到端比较，不是同候选的纯验证器比较。

| 指标 | 修改前同 50 题 | 本次 50 题 | 论文 GPT-5.5 目标 | 达标 |
|---|---:|---:|---:|---|
| 接受精度 | 78.95% | 76.92% | 100.0% | False |
| 决策准确率 | 79.17% | 75.86% | 86.7% | False |
| 覆盖率 | 52.00% | 60.00% | 70.1% | False |
| TA | 15 | 20 | — | — |
| FA | 4 | 6 | — | — |
| TR | 4 | 2 | — | — |
| FR | 1 | 1 | — | — |
| 弃答 | 24 | 20 | — | — |
| 正确性未决 | 2 | 1 | — | — |
| 运行错误 | 0 | 0 | — | — |
| 遗漏 | 0 | 0 | — | — |

上一轮相同 50 题结果完整保留：接受精度 78.26%、决策准确率 79.17%、覆盖率 50.00%，修改成功 = False。本轮只新增操作数精确表行的有界保留约束，原始事实、公式授权、计分、样本和模型不变。

按预先声明的严格口径：**修改成功 = False**。只在全部指标达标且 50 题完整、无运行错误时判为成功。

## 剩余问题

{"missing_or_ambiguous_filing_fact": 4, "no_usable_numeric_claim": 1, "verification_plan_has_no_roles": 7, "formula_authority_not_established": 3, "ambiguous_or_unresolved_registry_formula": 2, "candidate_generation_produced_no_usable_answer": 1, "missing_reporting_period": 1, "formula_output_dimension_mismatch": 1}

误接受/误拒绝案例完整保存于 `error_cases.json`；未修改金标或用较宽容差覆盖旧严格结果。

30 份接受/拒绝 SMT 证明重放一致；证明只确认给定约束的算术一致性。

原始 FinanceBench §4.1 采用人工标注并允许微小舍入误差，但未公开统一数值阈值。VeriFin §4.2 使用各数据集评分策略。因此原有严格“标签小数位”计分与论文人工口径存在未解决的可比性差异；本报告保留严格结果，不据此改记 100%。

- FinanceBench: https://arxiv.org/pdf/2311.11944
- VeriFin: https://arxiv.org/html/2608.10213v3

没有启动 67 题全量、其他数据集、其他骨干、baseline、repair 或训练。
