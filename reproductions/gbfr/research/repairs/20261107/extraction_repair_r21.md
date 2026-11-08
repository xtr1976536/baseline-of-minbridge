# R21 取数与约束表示修复

本智能体只做本地源审查、表示修复和单元验证；API调用0。全量暂停标记仍为true。原数据、金标、旧预测和R20评分代码未改变。

## 改动

- `table_structure_hints(context)`提供原文表头、列坐标、年份原文、行标签和近邻脚注，所有引用保留源字符偏移。它不挑金融数值，也不替换实体/时间/估值口径约束。
- 保留多层表头、单列“2019 and 2018”变化区间、同一Markdown块内的重复年度High/Low表头。保留空小计标签，单行金额表的第一列金额标记为numeric_first_column，不假冒指标标签。
- 对纯年份and枚举构造独立年度标量；对change/return/growth/range/duration类跨期指标保守保留单值区间，as-of和due等合取约束不拆分。
- 提示默认最多6表、48行标签/表、6表头/表、24列，总JSON12000字符。任何提示截断均有标记，原始D不截断。引擎已由执行链路智能体集成到OQA/OES，仅作定位辅助。

## 实际证据与反例

### TAT-QA:637fab7088ea6c78a5dba55f17e833bd_70c55e39fabb49df3f4b9691eeebcd09

2018 APAC binding incorrectly copied the 2019 cell 958744; the 2018 column is 937510. Hints preserve both date-header column positions, without supplying an answer or changing values.

原状态：answered；原预测：0.0。

### TAT-QA:7e10b02ae31ffbb6fed72213553ebe50_5bdc69be3f906fa7695fcc8c46e31bb9

Old category goals ask for one scalar over both 2018 and 2019. Pure independent-year enumeration now expands to annual scalars. Final counting must count categories meeting the condition, not six evidence objects.

原状态：abstained；原预测：None。

### TAT-QA:d80ea6ee60a1b1f11e971791784d7d6c_a23b3dcb820703a1d9aea7dc33091afb

Old extraction correctly found 12629 and 39119. Its score discrepancy is a difference/sign convention, not wrong-year extraction. Preserve each paired-year change column as one scope; do not split into annual values.

原状态：answered；原预测：-26490.0。

### FinQA:AMT/2016/page_49.pdf-1

Source restarts High/Low at 2015 within the same Markdown block after 2016. Hints expose header groups and row intervals. The old pipeline already extracted 101.88 and 93.21 correctly; its mismatch is sign convention, so no extraction gain is claimed.

原状态：answered；原预测：-8.510011778563017。

### FinQA:ETR/2011/page_301.pdf-1

Source has dates as columns and one row of financial values without an explicit row label. The first money cell must not become a metric label. Old source values 23596 and 63003 are correct; old mismatch is the sign convention for decrease, not wrong extraction.

原状态：answered；原预测：62.54781518340396。

## 验证边界

77项聚焦测试通过。R20 `metrics.py` 和 `units.py` 的SHA-256逐项匹配，无评分变化。

这里既保留明确抽错列的APAC资产案例，也保留Payroll、股价和MoneyPool旧取数本来正确的负对照；不会把其符号/口径差异冒称取数修复收益。

新表示对真实模型的效果须由根智能体至少20题端到端API测试确认。这个报告没有用gold反推取数，没有把缺失当0，也没有增添judge或correctness重试。

后续边界复验：`improvement`改为完整单词匹配，避免将`Improvements`和`Leasehold improvements`资产类别当作跨期变化；真正`Operating ratio improvement`仍保留单个跨期值。`test_refusal_repairs_r21.py`与`test_extraction_repairs_r21.py`联合36项通过，包括计数对象分组回归。
