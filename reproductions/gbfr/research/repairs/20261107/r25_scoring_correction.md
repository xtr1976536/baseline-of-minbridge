# R25 运行后评分器修正诊断

**这不是新的盲测，也没有重新运行推理模型。** 使用同一份冻结 R25 样本和预测，只对有原文依据的 currency-per-count 评分单位漏项作修正。预注册主表仍为 fixed2 **50%（5/10）**、reference_display **60%（6/10）**；没有写回或替换旧结果。

| 同一冻结预测 | 固定两位 | 金标展示位数 | 单位未判定 |
| --- | --- | --- | --- |
| 预注册评分器 | 50%（5/10） | 60%（6/10） | 1 |
| 运行后修正评分器诊断 | 60%（6/10） | 70%（7/10） | 0 |

唯一变化 ID：`FinQA:V/2010/page_28.pdf-1`。原模型输出和程序均未变，44.90353697749196 USD/transaction 原被标记单位未判定，现在按明确来源识别为美元/笔交易，数值在两种精度下均匹配。拒答召回仍是1/2=50%，可答误拒仍为0。DRE与BDX口径冲突等其他结果均不变。

## 来源与通用规则

问题明确问 average payment volume per transaction。表头 Payments Volume(billions)、Total Transactions(billions)，Visa行为$2793与62.2；原文把payments volume定义为aggregate dollar amount，并声明currency figures are in U.S. dollars。因此两输入十亿倍率相消，输出是USD/transaction。官方程序同样为divide(2793,62.2)。这不是根据答案大小猜倍率或追金标。

规则覆盖货币每 transaction、employee、item、unit；如revenue per employee、cost per item，须由最终请求中的货币量语义与明确币种声明共同支持。规范USD per transaction等货币单位别名，内部币种冲突会拒绝。普通时间/物理volume、count-per-count、百分率、每股数量仍各自处理；输入million不会继承为每笔输出倍率，显式输出thousand/million及官方展示尺度保留。

新增29项专项正反测试，包含独立employee/item例、错误币种、错误倍率、分母类型、Europe词界、来源不足/多币种、输入和输出尺度、百分率/count/per-share保护。聚焦153项通过、1项已知与评分无关的引擎测试未选中；根智能体随后运行全套测试。

## 冻结与解释边界

独立评分源码保存在`r25_scoring_source_snapshot/gbfr`，manifest记录哈希。预注册R25的results.json、samples.jsonl、predictions.jsonl、version.json哈希前后相同；原推理源码快照全部哈希匹配。API为0，未改金标或精度政策，未运行全量或TAT-QA。

修正诊断60%/70%反映已见样本的评分器能力修复，不能当成新盲测成绩或推理模型能力提高的证据。预注册50%/60%继续保留并作为本轮原始报告结果；本文件只提供运行后评分器修正的并列说明。
