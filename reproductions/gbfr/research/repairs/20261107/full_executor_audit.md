# 全量执行器错误审计

全量保持暂停，0 API请求；冻结R19真实程序经精确缓存重放。

全量12个技术错误中，1个服务余额错误未重放，1个ratio尺度错误属于单位适配，其余10个程序错误已逐个复现。
修复后8个程序可以执行；2个多年份输出仍保留为错误，未挑答案，也未改成成功拒答。执行成功不代表答案正确。

| 案例 | 原错误 | 新行为 | 说明 |
|---|---|---|---|
| FinQA:AMT/2014/page_160.pdf-2 | Unsupported scale: ratio | value=0.6105295118719062 | 程序执行本身正常；错误来自 output_meta.scale=ratio 的单位适配，由单位审计负责。 |
| FinQA:CB/2008/page_229.pdf-2 | Invalid generated Python syntax | value=77.0 | 删除唯一多余末尾花括号后原平均公式输出77，未改数值或运算。 |
| FinQA:SNA/2007/page_49.pdf-2 | Only one compute(vars) function is permitted | value=58.37837837837837 | 仅解包单键code包装；64.8/1.11仍输出58.378378百万股，与冻结金标58,909,091不同，不能靠包装修复纠正操作数。 |
| TAT-QA:4bf6297fe4aaf51d58b160a778fadc6f_82d14c3d4fe3414597b638431b2eeffc | Only arithmetic builtins and safe container methods may be called | error: compute returned non-scalar text | 原比较返回两个年份2019和2018；不能选择一个。题目文字signed threshold与金标2017存在解释冲突。 |
| TAT-QA:3e2109c375cbf670d40c77b22b430b20_0a5bf43b11e96289f11f5f5105b1da4a | compute returned non-scalar text | value=2018.0 | 仅在显式年份选择问题中，将模型已选定的唯一完整日期标签表示为其年份，并保留原标签；不改变比较运算或所选时期。 |
| TAT-QA:8c79671b7ad782c9d32167f2c04a1af5_6ad0bde371cfef66faf1970bb0c767cd | compute returned non-scalar text | value=2017.0 | 仅在显式年份选择问题中，将模型已选定的唯一完整日期标签表示为其年份，并保留原标签；不改变比较运算或所选时期。 |
| TAT-QA:902a9a9cf29ffa7b1434e0e604e0c8ea_16fb06cce05c75e5d065387003ae6622 | Invalid generated Python syntax | value=-5.6 | 删除唯一多余末尾花括号后仍输出-5.6，与正号金标不同；不擅自取绝对值。 |
| TAT-QA:7399b5db48b8dc118aa8f0c7336fffa3_445534e20d1dd84e1c0a6a94e107fed8 | compute returned non-scalar text | value=2019.0 | 仅在显式年份选择问题中，将模型已选定的唯一完整日期标签表示为其年份，并保留原标签；不改变比较运算或所选时期。 |
| TAT-QA:73842f616f18b30fe624ac4a4281a91d_56ff97230978b4ccbb32b8df028391c3 | Invalid generated Python syntax | value=-3498.0 | 删除唯一末尾回车图形符号后仍输出-3498，与正号金标不同；不擅自取绝对值。 |
| TAT-QA:e0e0f21500e31cabc36158bb0c05826a_4c76b32b0cbd412cb80e188a064343dc | Only arithmetic builtins and safe container methods may be called | error: compute returned non-scalar text | 原程序比较输入2014、2014、2.4，返回两个年份2019和2018；属于取数/多答案问题，不能由执行器修成标量。 |
| TAT-QA:057149f07d2fad98ce7387e82475f309_77361e6295e37b679affaa3fd5295dc5 | compute returned non-scalar text | value=2019.0 | 仅在显式年份选择问题中，将模型已选定的唯一完整日期标签表示为其年份，并保留原标签；不改变比较运算或所选时期。 |

## 通用适配边界

- 只解包严格单键 JSON code 对象；额外字段、任意散文和不完整代码不被修复。
- 只删除一个多余末尾花括号或回车图形符号，且结果必须已经是完整合法Python；不补操作符、数字、键、语句。
- 仅允许字符串字面量的join方法。多年份join结果仍不是标量，不选取首项。
- 仅调用方显式允许年份选择时，转换唯一完整有效日期/年份标签；不在文本中搜索年份、不补世纪、不把未知字符串当None。
- 保留生成程序、输入、SHA-256、旧错误、新结果、原始日期和有效程序；仍限制一个compute(vars)，禁止嵌套函数、import、文件/网络、eval/exec和私有属性，保留独立进程超时。

42项聚焦测试通过。worker.py无需改动；所有修复在父执行器表示校验层完成。
