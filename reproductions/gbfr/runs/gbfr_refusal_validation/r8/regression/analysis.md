# 拒答验证逐题诊断

版本：r8；套件：regression；只读分析，0 API 调用。

## FinQA

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |
|---|---|---|---:|---:|---|
| FinQA:JPM/2009/page_175.pdf-3 | in 2008 what was the ratio of the trading assets derivatives - receivables to the payables | answered | 1.3027575107296137 | 1.72 | incorrect_numeric_answer |
| FinQA:AMT/2008/page_107.pdf-2 | in 2006 what was percentage change in the employee separations liabilities | answered | -65.04794161141058 | -65.1% | incorrect_numeric_answer |
| FinQA:LMT/2015/page_89.pdf-4 | in november 2015 what was the percent of the costs associated with issuing of the notes under the 364-day facility used to finance the acquisition | abstained | None | 0.69% | false_abstention |
| FinQA:BKNG/2016/page_33.pdf-1 | at the measurement point december 312016 what was the ratio of the the priceline group inc . . to the nasdaqcomposite index | answered | 1.4475385610048952 | 1.44 | incorrect_numeric_answer |
| FinQA:ETR/2016/page_150.pdf-4 | what are the payments for the next three years on the entergy new orleans storm recovery bonds ( in millions? ) | answered | 32.8 | 44.4 | incorrect_numeric_answer |
| FinQA:SNA/2013/page_34.pdf-2 | what is the return on investment if $ 100 are invested in s&p500 at the end of 2008 and sold at the end of 2010? | answered | 0.4550999999999999 | 45.51 | incorrect_numeric_answer |
| FinQA:ANSS/2016/page_47.pdf-1 | as of december 31 , 2016 what was the percent of the company's significant contractual obligations for the global headquarters operating lease due in 2016 | abstained | None | 29.4% | false_abstention |
| FinQA:MRK/2013/page_125.pdf-2 | considering the years 2011-2013 , what is the average value of settlements? | abstained | None | 309.67 | false_abstention |
| FinQA:SNA/2013/page_84.pdf-3 | what percentage of trade and other accounts receivable are considered as doubtful receivables in 2013 | answered | 2.72644098810613 | 2.9% | incorrect_numeric_answer |
| FinQA:STT/2014/page_54.pdf-2 | what is the roi of an investment in state street corporation from 20011 to 2012? | error | None | -11.4% | technical_error |
| FinQA:JPM/2015/page_137.pdf-3 | without the foreign exchange hedges , what would the total net derivatives be , in millions? | answered | 25920.0 | 42500 | incorrect_numeric_answer |

## TAT-QA

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类型 |
|---|---|---|---:|---:|---|
| TAT-QA:771fd661a72d5018797f3ea240571013_c22c73c764d0e502810da5391f4538ad | What is the incentive compensation received by Messrs Richard, Robert and Bruce Leeds respectively? | abstained | None | 0 | false_abstention |
| TAT-QA:dba93cc78c71186db1facefa72346cd5_a28369b222ac578302e90a752aa79977 | In which year was Research and development expenses less than 50,000 thousands? | abstained | None | 2018 | false_abstention |
| TAT-QA:9fe2506a4389f5a61511c915c3323f10_f585885778f95bf1dbb2a00151125624 | What was the change in revenue in Ireland in 2019 from 2018? | abstained | None | 0 | false_abstention |

