# 固定小样本逐题诊断

轮次：r4；精度口径：reference_display；本脚本仅读取结果，不调用 API、不重跑失败题。

## FinQA

已处理 19/33；正确 9；Total Acc. 27.27%；正确拒答 0/3；技术错误 0。

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类别 |
|---|---|---|---|---|---|
| FinQA:JPM/2009/page_175.pdf-3 | in 2008 what was the ratio of the trading assets derivatives - receivables to the payables | answered | 1.3027575107296137 | 1.72 | incorrect_numeric_answer |
| FinQA:RCL/2016/page_6.pdf-2 | what was the anticipated percentage increase in the global cruise fleet berths from 2017 to 2021 | abstained | None | 34.4% | false_abstention |
| FinQA:AMT/2008/page_107.pdf-2 | in 2006 what was percentage change in the employee separations liabilities | answered | -65.04794161141058 | -65.1% | incorrect_numeric_answer |
| FinQA:BKNG/2016/page_33.pdf-1 | at the measurement point december 312016 what was the ratio of the the priceline group inc . . to the nasdaqcomposite index | answered | 1.4475385610048952 | 1.44 | incorrect_numeric_answer |
| FinQA:BLK/2012/page_33.pdf-2 | what is the percent change in equity component changes from 12/31/2011 to 12/31/2012? | answered | 27.40300869055477 | 27.4% | incorrect_numeric_answer |
| FinQA:ETR/2016/page_150.pdf-4 | what are the payments for the next three years on the entergy new orleans storm recovery bonds ( in millions? ) | answered | 32.8 | 44.4 | incorrect_numeric_answer |
| FinQA:SNA/2013/page_34.pdf-2 | what is the return on investment if $ 100 are invested in s&p500 at the end of 2008 and sold at the end of 2010? | answered | 45.50999999999999 | 45.51 | incorrect_numeric_answer |
| FinQA:ANSS/2016/page_47.pdf-1 | as of december 31 , 2016 what was the percent of the company's significant contractual obligations for the global headquarters operating lease due in 2016 | abstained | None | 29.4% | false_abstention |
| FinQA:MRK/2013/page_125.pdf-2 | considering the years 2011-2013 , what is the average value of settlements? | abstained | None | 309.67 | false_abstention |
| FinQA:SNA/2013/page_84.pdf-3 | what percentage of trade and other accounts receivable are considered as doubtful receivables in 2013 | answered | 2.72644098810613 | 2.9% | incorrect_numeric_answer |

## TAT-QA

已处理 18/33；正确 14；Total Acc. 42.42%；正确拒答 0/3；技术错误 0。

| 样本 | 问题 | 状态 | 预测 | 金标 | 问题类别 |
|---|---|---|---|---|---|
| TAT-QA:771fd661a72d5018797f3ea240571013_c22c73c764d0e502810da5391f4538ad | What is the incentive compensation received by Messrs Richard, Robert and Bruce Leeds respectively? | abstained | None | 0 | false_abstention |
| TAT-QA:37473c2794aadea84bf6a32fac8dbf59_a128d314dd89d86359ca8f3d53d20f07 | What is the percentage change in total segment net revenues between 2018 and 2019? | answered | -12.670080468178494 | -12.67 | incorrect_numeric_answer |
| TAT-QA:7f4f100eb8ea1c0d35ea646699df8978_56a23fdad76c4c725741a0689cbaf57a | What was the total gross receivables for credit ratings 1 to 4 in 2019? | abstained | None | 5,984 | false_abstention |
| TAT-QA:a8c11cade3237853c6a6869143f7ec37_32533d1bd67d1ad3e0d03442495e23f0 | What was the percentage change in the retail satellite TV net customer losses from 2018 to 2019? | abstained | None | 4.3% | false_abstention |

