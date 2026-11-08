# 全量错误修复：离线复验

**NOT full-pipeline fresh API verification. 0 API；不重规划、不重取证。**
固定40题为失败富集调试集，不是论文主实验分布；不得把以下分数称为真实端到端准确率。
原误拒且无最终程序的样本保持原预测；不补数值、不挑答案。技术错误仍是失败，不能算正确拒答。

| 数据集 | 模式 | 正确 / 20 | 该调试集得分 | 技术错误 | 误拒答 |
|---|---|---:|---:|---:|---:|
| FinQA | baseline | 5/20 | 25.00% | 3 | 6 |
| FinQA | rescored_only | 6/20 | 30.00% | 3 | 6 |
| FinQA | reexecuted | 8/20 | 40.00% | 0 | 6 |
| TAT-QA | baseline | 5/20 | 25.00% | 3 | 6 |
| TAT-QA | rescored_only | 10/20 | 50.00% | 3 | 6 |
| TAT-QA | reexecuted | 12/20 | 60.00% | 1 | 6 |

本集合无反事实题，因此拒答准确率未测，不能写成0%或100%。

baseline 使用冻结 R19 的评分及单位代码；rescored_only 的变化只说明评分适配差异；reexecuted 的变化才包含保存程序的格式/输出类型适配。
当前新的规划/证据提示词没有在本复验中被模型运行，其效果仍待真实API验证。

## 另列11个非服务技术错误

这些案例与40题有重叠，不能当作额外11道独立题合并计分。
| 案例 | 原错误 | 新执行状态 / 值 | 当前评分正确 |
|---|---|---|---|
| FinQA:AMT/2014/page_160.pdf-2 | Unsupported scale: ratio | answered / 0.6105295118719062 | True |
| FinQA:CB/2008/page_229.pdf-2 | Invalid generated Python syntax | answered / 77.0 | True |
| FinQA:SNA/2007/page_49.pdf-2 | Only one compute(vars) function is permitted | answered / 58.37837837837837 | False |
| TAT-QA:4bf6297fe4aaf51d58b160a778fadc6f_82d14c3d4fe3414597b638431b2eeffc | Only arithmetic builtins and safe container methods may be called | error / None | False |
| TAT-QA:3e2109c375cbf670d40c77b22b430b20_0a5bf43b11e96289f11f5f5105b1da4a | compute returned non-scalar text | answered / 2018.0 | True |
| TAT-QA:8c79671b7ad782c9d32167f2c04a1af5_6ad0bde371cfef66faf1970bb0c767cd | compute returned non-scalar text | answered / 2017.0 | True |
| TAT-QA:902a9a9cf29ffa7b1434e0e604e0c8ea_16fb06cce05c75e5d065387003ae6622 | Invalid generated Python syntax | answered / -5.6 | False |
| TAT-QA:7399b5db48b8dc118aa8f0c7336fffa3_445534e20d1dd84e1c0a6a94e107fed8 | compute returned non-scalar text | answered / 2019.0 | True |
| TAT-QA:73842f616f18b30fe624ac4a4281a91d_56ff97230978b4ccbb32b8df028391c3 | Invalid generated Python syntax | answered / -3498.0 | False |
| TAT-QA:e0e0f21500e31cabc36158bb0c05826a_4c76b32b0cbd412cb80e188a064343dc | Only arithmetic builtins and safe container methods may be called | error / None | False |
| TAT-QA:057149f07d2fad98ce7387e82475f309_77361e6295e37b679affaa3fd5295dc5 | compute returned non-scalar text | answered / 2019.0 | True |

原始程序、inputs、SHA、阶段证明和输出适配trace在 cases / results JSON中保留。
读前验证了子集SHA、源日志SHA、冻结R19源码和配置SHA、子集与data/main的逐行相同关系；代码运行中发生修改会拒绝冻结。
全量日志和旧源码均未修改。当前源码与冻结R19评分源码另存，保证新旧口径可复查。
