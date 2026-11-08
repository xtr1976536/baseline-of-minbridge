# OQA / OPE.final 新契约的论文一致性复核

结论：题目明确以数量和单价描述价值时，最终求两期价值之差，允许必要的两个乘积再做外层差值，符合附录 F 的证据约束与基本算术意图。没有发现新文本明确允许绕过 OMD 发明财务公式。此为只读文本审查，0 API调用，不代表修复实测成功。

## 论文依据

- PDF第5页，§4.1 OQA（research/paper.txt约255–284行）：function描述final aggregation logic，subgoals定义计算所需证据；五类推理涵盖基本算术、统计聚合、时间推理。
- PDF第6页，Algorithm 1第8行：Apply operator Op on Vresults。同期OPE段落要求使用符号路径和verified evidence，任何输入缺失都传播⊥。
- PDF第15页，附录C表5：ArithmeticCalculation从query里的算术关系抽取明确操作数，Op列出加减乘除；这张表没有给出完整嵌套表达式编码语法。
- PDF第17页，附录F Question Analysis（约887–943行）：只抽取所需操作数，不在OQA中计算；明确包含weighted average when implied。加权平均自然需要乘积、求和和除法，故“operator=average时只能出现mean或加法”的旧限制没有论文依据。
- PDF第19页，附录F指标程序（约1028–1070行）：代码从给定财务指标公式生成；这支持命名财务派生指标继续走OMD/OPE.metric。
- PDF第20页，附录F最终程序（约1072–1125行）：传入query/context/type/evidences，返回compute(vars)的value和trace；允许basic arithmetic和weighted average，没有“只能使用一次所选运算符”的限制。

## 必须保留的解释边界

“外层operator+必要基本中间算术”应明示为与附录F一致的本地实现解释，不能声称是论文逐字规定。Algorithm 1和表5仅给抽象的Op(Vresults)。它不是允许任意复合金融定义的通行证。

当前已看到的守卫包括：命名财务指标保留为OMD子目标；仅Q/D请求或给出的基本关系可执行；不能因为Total/Average/Net/Value字样就覆盖已识别的财务概念；量价口径必须匹配，行权价不等于期权公允价值。新inventory示例明确给定数量和单价，满足这一边界。

建议再写明：金融观测值必须通过已解决的vars输入，不能从完整context中捡一个未经过OES的金额硬编码进最终程序。题目给定阈值、图中数学系数、标准单位换算可以作为相应常数；其来源应可追踪。不得把“需要中间算术”当成补齐缺失金融操作数、CAGR/估值定义或外推假设的理由。附录F允许的时间归一化仍可在其明确时间范围和证据下执行，不能被一概误禁。

## 14条普通算术复查线索分组

### 聚合/平均（6）

- FinQA:ALXN/2016/page_153.pdf-2
- FinQA:PNC/2014/page_111.pdf-2
- FinQA:JPM/2009/page_175.pdf-5
- FinQA:UNP/2009/page_35.pdf-2
- FinQA:LMT/2014/page_91.pdf-4
- TAT-QA:e641836950c1db8da4260bb7842d1242_ae10d06f4a7b08fdc13138ec794ee3c5

### 数量×匹配的单位价值（3）

- FinQA:GPN/2010/page_89.pdf-4
- FinQA:HWM/2018/page_96.pdf-2
- FinQA:GPN/2013/page_87.pdf-3

### 增长、差值或区间回报（4）

- FinQA:BLL/2012/page_31.pdf-4
- FinQA:ETR/2004/page_212.pdf-4
- FinQA:BKNG/2016/page_33.pdf-3
- TAT-QA:22be2fdb6d29626851b25f7a53fada57_6769cc0cee475e77d8eb292b9bdefd81

### 普通比值（1）

- TAT-QA:42e150a81c12286dac3083899a6488b1_653397f888b9461a9d37b7bc372cc33b

这些是基于原始计划和缺失说明的复查线索，未根据金标替模型补计划，也未声称已成功修复。

另有ABMD/2007/page_78.pdf-2的appreciation-factor问题不在上述14条启发式集合内：仅当Q/D给出或直接蕴含复用增长关系时才属于基本算术，不能从金标反推采用哪一种增长约定。
