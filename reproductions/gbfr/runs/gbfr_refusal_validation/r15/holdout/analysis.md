# 拒答验证逐题诊断

版本：r15；套件：holdout；只读分析，0 API 调用。

## FinQA

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |
|---|---|---|---:|---:|---|
| FinQA:ETR/2017/page_143.pdf-3 | what is the amount of interest applied to the annual long-term debt maturities in 2018? | abstained | None | 566808000 | false_abstention |
| FinQA:counterfactual:20 | What is the effective interest rate for long-term debt and other long-term liabilities in 2014? | error | None | None | technical_error |
| FinQA:counterfactual:77 | what was the difference in operating margin between 2016 and 2017? | error | None | None | technical_error |
| FinQA:counterfactual:86 | In 2013, what was the percent of the allowances for doubtful accounts for Makita Corporation? | error | None | None | technical_error |

## TAT-QA

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |
|---|---|---|---:|---:|---|
| TAT-QA:0dfb4455ae2e1b2066e99d9a3a05baf0_4c8709f777694f5ea71b7c56a0080bfa | What was the amortization expense for the twelve months ended December 31, 2019 in 2018? | abstained | None | 163 | false_abstention |
| TAT-QA:counterfactual:14 | What is the change in Goodwill from 2018 to 2019? | error | None | None | technical_error |

