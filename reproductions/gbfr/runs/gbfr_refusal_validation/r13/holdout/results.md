# GBFR 拒答小样本验证

套件：holdout；题数：30；仅用户指定的 GPT-5.6 Sol；全量未授权。
执行方式：仅重放既有真实响应缓存，禁止联网；缺失响应保留为错误。

| 数据集 | 已处理 | 正确拒答 | 拒答准确率 | 可回答对照：作答/总数 | 对照正确 | 误拒答 | 错误 |
|---|---:|---:|---:|---:|---:|---:|---:|
| FinQA | 15/15 | 7/10 | 70.00% | 4/5 | 3 | 1 | 3 |
| TAT-QA | 15/15 | 9/10 | 90.00% | 4/5 | 4 | 1 | 1 |

Focus is diagnostic only. Holdout has enriched negatives, so its Total Acc. is not compared as a paper-distribution main score. Errors never count as correct abstentions.

拒答专项检查：未通过。
原66题主实验门槛：未通过或不适用于此套件。
