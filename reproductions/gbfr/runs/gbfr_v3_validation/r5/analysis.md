# 固定小样本逐题诊断

轮次：r5；精度口径：reference_display；本脚本仅读取结果，不调用 API、不重跑失败题。

## FinQA

已处理 21/33；正确 12；Total Acc. 36.36%；正确拒答 0/3；技术错误 0。

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类别 |
|---|---|---|---|---|---|
| FinQA:JPM/2009/page_175.pdf-3 | in 2008 what was the ratio of the trading assets derivatives - receivables to the payables | answered | 1.3027575107296137 | 1.72 | incorrect_numeric_answer |
| FinQA:AMT/2008/page_107.pdf-2 | in 2006 what was percentage change in the employee separations liabilities | answered | -65.04794161141058 | -65.1% | incorrect_numeric_answer |
| FinQA:STT/2007/page_111.pdf-1 | what is the percentage change in the the balance of cash and u.s . government securities from 2006 to 2007? | abstained | None | 8.6% | false_abstention |
| FinQA:BKNG/2016/page_33.pdf-1 | at the measurement point december 312016 what was the ratio of the the priceline group inc . . to the nasdaqcomposite index | answered | 1.4475385610048952 | 1.44 | incorrect_numeric_answer |
| FinQA:ETR/2016/page_150.pdf-4 | what are the payments for the next three years on the entergy new orleans storm recovery bonds ( in millions? ) | answered | 32.8 | 44.4 | incorrect_numeric_answer |
| FinQA:SNA/2013/page_34.pdf-2 | what is the return on investment if $ 100 are invested in s&p500 at the end of 2008 and sold at the end of 2010? | abstained | None | 45.51 | false_abstention |
| FinQA:ANSS/2016/page_47.pdf-1 | as of december 31 , 2016 what was the percent of the company's significant contractual obligations for the global headquarters operating lease due in 2016 | answered | 10.29181802872471 | 29.4% | incorrect_numeric_answer |
| FinQA:MRK/2013/page_125.pdf-2 | considering the years 2011-2013 , what is the average value of settlements? | answered | -309.6666666666667 | 309.67 | incorrect_numeric_answer |
| FinQA:SNA/2013/page_84.pdf-3 | what percentage of trade and other accounts receivable are considered as doubtful receivables in 2013 | answered | 2.72644098810613 | 2.9% | incorrect_numeric_answer |

## TAT-QA

已处理 29/33；正确 25；Total Acc. 75.76%；正确拒答 0/3；技术错误 0。

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类别 |
|---|---|---|---|---|---|
| TAT-QA:771fd661a72d5018797f3ea240571013_c22c73c764d0e502810da5391f4538ad | What is the incentive compensation received by Messrs Richard, Robert and Bruce Leeds respectively? | abstained | None | 0 | false_abstention |
| TAT-QA:a8c11cade3237853c6a6869143f7ec37_276815a7f82a8c5eb1a4991d98fe253b | What is the change in the number of IPTV retail subscribers in 2019? | abstained | None | 91476 | false_abstention |
| TAT-QA:37473c2794aadea84bf6a32fac8dbf59_a128d314dd89d86359ca8f3d53d20f07 | What is the percentage change in total segment net revenues between 2018 and 2019? | abstained | None | -12.67 | false_abstention |
| TAT-QA:a8c11cade3237853c6a6869143f7ec37_32533d1bd67d1ad3e0d03442495e23f0 | What was the percentage change in the retail satellite TV net customer losses from 2018 to 2019? | answered | -4.267575170064215 | 4.3% | incorrect_numeric_answer |

