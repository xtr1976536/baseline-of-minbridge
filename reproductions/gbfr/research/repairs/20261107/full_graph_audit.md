# 全量误拒答的图谱名称与源公式审计

覆盖全部110道误拒答；0 API请求。图资产与旧预测未改。

## 结论

没有提交“派生优先”或按答案恢复公式。运行时精确名称优先并非这里的充分修复点：多个节点的软别名交叉冲突，部分原子节点是重建时排除了自身源公式，而非本来没有公式。

全图共380个原子名称又被派生节点列为软别名；其中没有一组具有完全相同且非空的定义，也没有原子规范名被派生节点列为强 primary_alias。不能只按是否有公式选择名称。

## 110题覆盖统计

| 审查旗标（可重叠，不等于已证明的主因） | 案例数 |
|---|---:|
| directly_missing_atomic_has_derived_soft_alias | 7 |
| directly_missing_atomic_has_excluded_source_formula | 7 |
| contains_unbound_goal_name | 79 |
| ordinary_arithmetic_planning_review_candidate | 14 |
| contains_resolved_derived_goal | 21 |

普通多步基本算术候选是按未绑定顶层目标及OES明确提及组成值/计算来筛查的复查线索，不等于所有未知指标都应扩充图谱。根任务正在处理这些规划问题。

## Debt-to-Asset Ratio 的源证据

- 冻结图中该精确名称是 atomic，来源原始记录5；其源公式 `(Total Liabilities ÷ Total Assets) ×100%` 实际存在。
- 静态代码使用 `liabilities`、`assets`，绑定成独立的 Liabilities、Assets；原公式使用 Total Liabilities、Total Assets。重建记录以 `input_metric_identity_needs_review` 排除。
- 这是缺少输入身份/限定词证明，不是表达式语法解析错误。仅凭公式外形相同、参数位置相同不能删掉 Total 等限定词。没有足够证据把该排除通用地改为接受。
- 可替代软别名 Debt Ratio、Debt-to-Assets Ratio 自身同时含 Total Debt/Total Assets 和 Total Liabilities/Total Assets，不能为了某个答案将它们等同。

其他危险例子：Net Revenue 与 Net Operating Income/Net Sales 等软别名冲突；Tax Rate 与 Effective Tax Rate 区分法定税率/实际税率；Total Cash Dividends 与 Total Dividends of Previous Year 带期间差异。

## 可明确定位的资产局限

以下案例的直接缺失原子目标自身在原始FMKG有被排除的公式（需源码/专家重建，尚未修复）：

- FinQA:UAA/2016/page_42.pdf-2
- FinQA:AMAT/2013/page_37.pdf-2
- FinQA:SNA/2013/page_83.pdf-1
- FinQA:ETR/2017/page_143.pdf-3
- FinQA:BLL/2006/page_67.pdf-1
- TAT-QA:7bc6da25adaae100b2983a53464947c1_77efeb39d0b7249a3501f2f182d21679
- TAT-QA:7bc6da25adaae100b2983a53464947c1_6b607bd54f6a20e38c565139ea23aca8

以下顶层未知目标有普通算术规划错误线索，不应自动补入金融知识图：

- FinQA:ALXN/2016/page_153.pdf-2
- FinQA:BLL/2012/page_31.pdf-4
- FinQA:GPN/2010/page_89.pdf-4
- FinQA:PNC/2014/page_111.pdf-2
- FinQA:HWM/2018/page_96.pdf-2
- FinQA:JPM/2009/page_175.pdf-5
- FinQA:ETR/2004/page_212.pdf-4
- FinQA:GPN/2013/page_87.pdf-3
- FinQA:UNP/2009/page_35.pdf-2
- FinQA:BKNG/2016/page_33.pdf-3
- FinQA:LMT/2014/page_91.pdf-4
- TAT-QA:22be2fdb6d29626851b25f7a53fada57_6769cc0cee475e77d8eb292b9bdefd81
- TAT-QA:e641836950c1db8da4260bb7842d1242_ae10d06f4a7b08fdc13138ec794ee3c5
- TAT-QA:42e150a81c12286dac3083899a6488b1_653397f888b9461a9d37b7bc372cc33b

已通过完整图载入和DAG/公式检查；实际记录5的绑定与排除原因已作断言验证。没有新建候选资产，因为尚无足以证明限定词等价的安全通用恢复规则。

图SHA-256保持：`094871c783c318541ede74750f944ff61622cb3de7d2317b1609792f1b34f28a`。逐题目标、候选定义/公式和源排除详情在同名JSON中。

现有图谱恢复回归测试：`tests/test_graph_recovery.py` 11项通过。未改运行时名称解析和重建代码。
