# 拒答验证逐题诊断

版本：r11；套件：holdout；只读分析，0 API 调用。

## FinQA

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |
|---|---|---|---:|---:|---|
| FinQA:ETR/2017/page_143.pdf-3 | what is the amount of interest applied to the annual long-term debt maturities in 2018? | abstained | None | 566808000 | false_abstention |
| FinQA:AWK/2018/page_146.pdf-2 | at what price per share did awk repurchase its shares of common stock in 2017? | answered | 77.14285714285715 | 77.1 | incorrect_numeric_answer |
| FinQA:counterfactual:86 | In 2013, what was the percent of the allowances for doubtful accounts for Makita Corporation? | answered | -2.72644098810613 | None | false_answer_on_counterfactual |

## TAT-QA

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |
|---|---|---|---:|---:|---|
| TAT-QA:0dfb4455ae2e1b2066e99d9a3a05baf0_4c8709f777694f5ea71b7c56a0080bfa | What was the amortization expense for the twelve months ended December 31, 2019 in 2018? | abstained | None | 163 | false_abstention |
| TAT-QA:f16c6fb645e7d077e776af63a85a6643_44408c045f44fc6d7f892bc6b45e0251 | Which year had a larger amount of restricted stock and restricted stock unit awards granted? | answered | 2018.0 | 2018 | incorrect_numeric_answer |

