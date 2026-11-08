# GBFR 拒答小样本验证

套件：regression；题数：66；仅用户指定的 GPT-5.6 Sol；全量未授权。

| 数据集 | 已处理 | 正确拒答 | 拒答准确率 | 可回答对照：作答/总数 | 对照正确 | 误拒答 | 错误 |
|---|---:|---:|---:|---:|---:|---:|---:|
| FinQA | 33/33 | 3/3 | 100.00% | 26/30 | 20 | 3 | 1 |
| TAT-QA | 33/33 | 3/3 | 100.00% | 28/30 | 26 | 1 | 1 |

Focus is diagnostic only. Holdout has enriched negatives, so its Total Acc. is not compared as a paper-distribution main score. Errors never count as correct abstentions.

拒答专项检查：未通过。
原66题主实验门槛：未通过或不适用于此套件。
