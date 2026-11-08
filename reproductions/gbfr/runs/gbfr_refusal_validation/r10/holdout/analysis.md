# 拒答验证逐题诊断

版本：r10；套件：holdout；只读分析，0 API 调用。

## FinQA

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |
|---|---|---|---:|---:|---|
| FinQA:ETR/2017/page_143.pdf-3 | what is the amount of interest applied to the annual long-term debt maturities in 2018? | abstained | None | 566808000 | false_abstention |
| FinQA:AWK/2018/page_146.pdf-2 | at what price per share did awk repurchase its shares of common stock in 2017? | abstained | None | 77.1 | false_abstention |
| FinQA:counterfactual:86 | In 2013, what was the percent of the allowances for doubtful accounts for Makita Corporation? | error | None | None | technical_error |

## TAT-QA

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |
|---|---|---|---:|---:|---|
| TAT-QA:5ab28959bcbe242dd96ee7c64c2fc656_15c13aff533786d03238eb3e6f433c1f | What are leasehold improvements in 2019 as a percentage of the total property equipment before depreciation, amortization and fixed assets not in service? | abstained | None | 4.41 | false_abstention |
| TAT-QA:3c70a27ee159768e51821887c914a814_fa9aaeae1690c3b2a3c35aa57c14378e | How many % does provisions make up out of the total deferred tax assets? | error | None | 4.42 | technical_error |
| TAT-QA:f16c6fb645e7d077e776af63a85a6643_44408c045f44fc6d7f892bc6b45e0251 | Which year had a larger amount of restricted stock and restricted stock unit awards granted? | answered | 2018.0 | 2018 | incorrect_numeric_answer |

