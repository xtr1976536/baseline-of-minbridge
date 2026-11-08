# ReAct：HotpotQA 复现

## 1. 复现范围与状态

已完成 HotpotQA 500 题的 ReAct 实验，使用 gpt-5.6-sol 和作者 Wikipedia 检索环境。

## 2. 复现结果

| 数据集 | 样本数 | 正确数 | 本次 EM | 论文 GPT-3 EM | 论文 PaLM-540B EM | 本次 F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HotpotQA dev | 500 | 246 | **49.20%** | 30.8% | 27.4% | **64.90%** |

GPT-3 对应论文附录 Table 5 的 text-davinci-002；PaLM-540B 对应正文 Table 1 的纯 ReAct。模型参数和环境观察见实验配置与日志。题单采用作者 seed 233：7,405 道开发题打乱后取前 500 题。原 34 题保留，剩余 466 题由 4 个独立进程运行，题内顺序执行。

## 3. 方法与适配

作者notebook函数和示例保持不变，前置小的Chat续写格式说明，记录原始prompt与实际请求。max_tokens100、temperature0、top_p1、逐步stop和7步上限保留。模型伪造的Observation本地截断，真实观察只由环境返回。完全相同的整段重复可以去重。模糊格式交给作者已有动作重试/无效动作路径。

本轮Wiki页面中的反斜杠触发作者unicode-escape错误，仅UnicodeError时保留原始Unicode网页文本。Wikipedia请求补User-Agent和超时。403和格式故障恢复、适配变化都有记录。

## 4. 安装与运行

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

## 5. 代码、实验和日志

`experiments/react/hotpotqa/`包含：500题合并预测和完整轨迹、原34题记录、4个分片的API原响应/适配输出/环境日志、配置、恢复事件和运行日志。重复prompt采用标准gzip压缩，Python gzip或gzip -dc可读。

`summary.json`是唯一主结果；初始和分片 summary 分别记录各自局部结果。44次作者格式重试，1690条已保存API记录含中断尝试；手工中止时少量在途响应可能没落盘，计数范围为已保存的响应。

## 6. 离线验证

第一轮：HotpotQA题单/500个gold/EM/F1重新核验、34题保持不变、分片互斥完整、1690个已保存请求对应验证、ReAct单元检查。
第二轮：从暂存区建立不含.env的干净副本，重新检出固定作者子模块，再跑相同验证与测试。

返回[项目总览](../../README.md)。
