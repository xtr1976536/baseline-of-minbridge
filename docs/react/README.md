# ReAct：本项目复现完成范围

本项目只保留 **HotpotQA 500题**作为ReAct的通路与指标验证，不继续FEVER、ALFWorld、WebShop全量；研究重点是后续金融数值推理。HotpotQA本身是Wikipedia多跳问答，不能据其成绩宣称已验证金融数值推理或原论文全部任务。

## 最终结果

- EM **49.20%（246/500）**，F1 **64.90%**。
- 参考：论文附录text-davinci-002为30.8% EM；正文PaLM-540B纯ReAct为27.4%。不同底座/表格分开，不混用CoT-SC混合成绩。
- 模型：沿用本项目.env配置的gpt-5.6-sol Chat API。原作者模型标签text-davinci-002。
- 作者seed233、7405开发题随机打乱后的前500题。原34题不变，剩余466题用4个独立进程/环境运行，题内顺序执行。

## 最终代码与使用

```bash
# 本机密钥仍放未跟踪的.env，环境变量优先。沿用仓库Python环境。
# 从零开始：只HotpotQA 500题，4个独立进程
.venv/bin/python scripts/run_hotpotqa_parallel.py
# 小样本，串行
.venv/bin/python scripts/run_react.py --task hotpotqa --limit 10
# 明确续跑本机本次目录（配置/适配器指纹须一致）
.venv/bin/python scripts/run_hotpotqa_parallel.py --resume results/<本次并行目录>
# 已有已完成题，可保留后只补余下
.venv/bin/python scripts/run_hotpotqa_parallel.py --source results/<旧500题运行目录>
# 发布数据核验：零模型调用、零搜索请求
.venv/bin/python scripts/verify_react_release.py
.venv/bin/python -m unittest discover -s tests -p 'test_react*.py' -v
```

作者notebook函数和示例保持不变，前置小的Chat续写格式说明，记录原始prompt与实际请求。max_tokens100、temperature0、top_p1、逐步stop和7步上限保留。模型伪造的Observation本地截断，真实观察只由环境返回。完全相同的整段重复可以去重；不同动作不择优。模糊格式交给作者已有动作重试/无效动作路径。

本轮Wiki页面中的反斜杠触发作者unicode-escape错误，仅UnicodeError时保留原始Unicode网页文本。Wikipedia请求补User-Agent和超时，观察事实与奖励不替换。403和格式故障恢复、适配变化都有记录；不能把运行表述为无中断、实现从未变动的盲测。

## 证据包

`experiments/react/hotpotqa/`包含：500题合并预测和完整轨迹、原34题记录、4个分片的API原响应/适配输出/环境日志、配置、恢复事件和运行日志。重复prompt采用标准gzip压缩，Python gzip或gzip -dc可读。paths已脱敏，API密钥和.env不上传。

`summary.json`是唯一主结果；初始/分片summary仅对应各自局部范围，不能重复相加当新实验。44次作者格式重试，1690条已保存API记录含中断尝试；手工中止时少量在途响应可能没落盘，不等同供应商完整计费计数。

## 两轮检查

第一轮：HotpotQA题单/500个gold/EM/F1重新核验、34题保持不变、分片互斥完整、1690个已保存请求对应验证、ReAct单元检查。
第二轮：从暂存区建立不含.env的干净副本，重新检出固定作者子模块，再跑相同验证与测试。其他模型的已提交文件不纳入本次提交，也不重新运行付费实验。

不通过HotpotQA成绩证明金融任务效果；将来在同一金融数据/预算/工具下评测属于新的实验。
