# R21 repair固定队列的旧日志基线

仅使用R19原全量的预测；在全新Python解释器中分别使用冻结R19、冻结R20评分模块。没有调用API、重新规划/提取/执行程序或改动旧结果。旧日志重评分不是R21效果。

| 数据集 | manifest类别 | 原全量已测/选定 | R19原评分正确 | 冻结R20重评分正确 | 误拒答 | 技术错误 | 未测 |
|---|---|---:|---:|---:|---:|---:|---:|
| FinQA | ordinary_misrefusal | 3/3 | 0 | 0 | 3 | 0 | 0 |
| FinQA | graph_gap_misrefusal | 1/1 | 0 | 0 | 1 | 0 | 0 |
| FinQA | numeric_failure | 2/2 | 0 | 0 | 0 | 0 | 0 |
| FinQA | known_correct | 2/2 | 2 | 2 | 0 | 0 | 0 |
| FinQA | counterfactual_safety | 0/2 | 0 | 0 | 0 | 0 | 2 |
| TAT-QA | ordinary_misrefusal | 3/3 | 0 | 0 | 3 | 0 | 0 |
| TAT-QA | graph_gap_misrefusal | 1/1 | 0 | 0 | 1 | 0 | 0 |
| TAT-QA | numeric_failure | 2/2 | 0 | 0 | 0 | 0 | 0 |
| TAT-QA | known_correct | 2/2 | 2 | 2 | 0 | 0 | 0 |
| TAT-QA | counterfactual_safety | 0/2 | 0 | 0 | 0 | 0 | 2 |

两数据集各8道原始题在R19全量中有预测；各2道反事实安全题未在R19原全量处理，故拒答准确率未定义，不填写0%或100%。没有借用较早小样本的反事实预测。

各数据集已测原始题汇总：

- FinQA：8道已测；R19评分 2/8，冻结R20重评分 2/8；误拒4，技术错误0，反事实未测2。
- TAT-QA：8道已测；R19评分 2/8，冻结R20重评分 2/8；误拒4，技术错误0，反事实未测2。

该队列专门富集已知失败，不能拿其总准确率与论文主实验分布对比。所有题目ID、类别、原预测和两种冻结判定均保存在同名JSON。
