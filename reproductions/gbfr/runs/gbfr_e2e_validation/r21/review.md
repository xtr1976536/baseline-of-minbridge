# GBFR真实API修复验证复核

轮次r21；真实新OQA独立题数40；完整预测40/40；状态finished。

Total=(可回答题数值正确+不可回答题正确拒答)/所有题；Abst.=不可回答题正确拒答/不可回答题。技术错误按失败计入，不等于拒答。

## 事前固定的未使用题（20题）

| 数据集 | Total | 论文GPT-5 Total | 差值pp | Abst. | 论文GPT-5 Abst. | 差值pp | 误拒 | 技术错误 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FinQA | 60.00% (6/10) | 84.98% | -24.98 | 100.00% (2/2) | 98.80% | +1.20 | 1 | 0 |
| TAT-QA | 100.00% (10/10) | 95.75% | +4.25 | 100.00% (2/2) | 96.69% | +3.31 | 0 | 0 |

## 全部40题描述性汇总（含故障富集回归）

| 数据集 | Total | Abst. | 可回答题正确 | 误拒 | 技术错误 |
|---|---:|---:|---:|---:|---:|
| FinQA | 55.00% (11/20) | 100.00% (4/4) | 7/16 | 3 | 0 |
| TAT-QA | 85.00% (17/20) | 100.00% (4/4) | 13/16 | 0 | 0 |

## 回归题按修复类别比较

旧基线是R19真实预测在冻结R20评分下的结果；不是新增API。旧反事实未跑，不补成0或100%。

| 数据集 | 类别 | 旧正确/已测 | 新正确/已测 | 旧误拒 | 新误拒 |
|---|---|---:|---:|---:|---:|
| FinQA | ordinary_misrefusal | 0/3 | 1/3 | 3 | 2 |
| FinQA | graph_gap_misrefusal | 0/1 | 0/1 | 1 | 0 |
| FinQA | numeric_failure | 0/2 | 0/2 | 0 | 0 |
| FinQA | known_correct | 2/2 | 2/2 | 0 | 0 |
| FinQA | counterfactual_safety | 未测 | 2/2 | 0 | 0 |
| TAT-QA | ordinary_misrefusal | 0/3 | 2/3 | 3 | 0 |
| TAT-QA | graph_gap_misrefusal | 0/1 | 1/1 | 1 | 0 |
| TAT-QA | numeric_failure | 0/2 | 0/2 | 0 | 0 |
| TAT-QA | known_correct | 2/2 | 2/2 | 0 | 0 |
| TAT-QA | counterfactual_safety | 未测 | 2/2 | 0 | 0 |

## 未通过题（全部保留）

- evaluation / FinQA:MKTX/2004/page_99.pdf-2：abstained，输出None，参考8.3%；At least one required subgoal could not be grounded
- evaluation / FinQA:KHC/2018/page_132.pdf-1：answered，输出3664.0，参考10；需审查证据、口径或最终运算
- evaluation / FinQA:CDNS/2018/page_66.pdf-2：answered，输出20.12709283914066，参考25%；需审查证据、口径或最终运算
- evaluation / FinQA:AMT/2012/page_50.pdf-4：answered，输出46.0，参考45984064；需审查证据、口径或最终运算
- repair / FinQA:PNC/2014/page_111.pdf-2：abstained，输出None，参考-85；At least one required subgoal could not be grounded
- repair / FinQA:ALXN/2016/page_153.pdf-2：abstained，输出None，参考114%；At least one required subgoal could not be grounded
- repair / FinQA:ETR/2017/page_143.pdf-3：answered，输出56680.8，参考566808000；需审查证据、口径或最终运算
- repair / FinQA:AWK/2012/page_117.pdf-3：answered，输出0.040264，参考40264；需审查证据、口径或最终运算
- repair / FinQA:AWK/2017/page_148.pdf-1：answered，输出8.352941176470589，参考-8.4%；需审查证据、口径或最终运算
- repair / TAT-QA:42e150a81c12286dac3083899a6488b1_653397f888b9461a9d37b7bc372cc33b：answered，输出8.894005384526777，参考3.92；需审查证据、口径或最终运算
- repair / TAT-QA:d8c8ea72ed23e9f7d91c970e088a9413_6f1652507bcbc0845aa582d579321209：answered，输出-748.0，参考748；需审查证据、口径或最终运算
- repair / TAT-QA:7650d42c0b8ee9e5720698566b70419b_4639643a74b939b815419a6cf3245590：answered，输出-14.0，参考14%；需审查证据、口径或最终运算

## 复核限制与保存

用户选择GPT-5.6 Sol；论文参考为GPT-5，且使用作者未完整公开的最终图谱。本次为独立保守重建候选。
每个数据集每个集合只有2道不可回答题；100%只代表2/2，无法据此证明达到论文约97–99%的全量拒答能力。
未使用题由固定哈希事前抽取；回归题是故障富集样本。全部40题合并值仅作描述，不替代未使用题结果或论文主实验。
不按结果换题、删失败、改金标或按正确率重试。上述数值含技术错误；不单报成功调用分数。
全量保持暂停：True；旧全量两份journal未改：True；源码与冻结版本一致：True。
