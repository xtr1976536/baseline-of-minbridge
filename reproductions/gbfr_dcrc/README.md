# GBFR / DCRC 主模型复现

独立子项目；不修改旧 Logic-LM / ReAct 的环境、脚本、结果与后台任务。

## 当前状态

- GBFR：固定官方仓库 e1c1704eacfb8a3a522999d4a0ea726189bf5482，使用 submodule 保留上游；独立 Python 3.12 环境与独立 Neo4j（Bolt 17687，HTTP 17474）。主流程沿用官方 operators / agents；API transport 从环境读取密钥并记录逐调用原始响应。入口遍历全部数据，不使用官方 main.py 的随机 50 条抽样。单条联通验收前，官方图谱导入失败，详见下文。
- DCRC：按用户 2026-10-30 回复，SFT+GRPO 训练延后到 Kaggle。当前仅有论文执行器和训练参数清单，**不是训练完成的 DCRC，也没有主实验准确率**。
- 本目录不运行其他模型的 baseline、消融、敏感性、额外审计对比或线上 A/B 实验。

## 原文与来源

- GBFR: https://aclanthology.org/2026.acl-long.1273/ ，代码 https://github.com/aolaoban/Graph-Bounded_Financial_Reasoning
- DCRC: https://arxiv.org/abs/2605.31064 ，截至核查未找到作者公开代码、构造后的训练集、训练后 DSA checkpoint。基础 Qwen2.5 开源不等于已获得 DCRC 权重。

## 主实验协议

GBFR 对应 Table 1 的 GBFR 行：FinQA、TAT-QA、FinanceReasoning、CFBenchmark；指标 Total Accuracy 与无答案子集 Abstention Accuracy；参考底座 GPT-5 / Qwen3-14B。当前服务模型 gpt-5.6-sol 为替代底座，不能宣称精确复现原得分。

DCRC 对应 Table 1 的 DSA-1.5B / 3B / 7B 行：FinQA dev/test、ConvFinQA dev，Execution Accuracy（论文 1% 容差）。需要先构造对抗数据，再完成 structure-aware SFT 和 GRPO，之后评估。

## 已确认的数据和实现差异

详见 `results/data_audit.json`（每文件 SHA256 与样本数）。官方 release：FinQA 1050+97=1147，论文 Table 4 为 1002+97=1099；TAT-QA 1663+151=1814，论文为1119+151=1270。FinanceReasoning 2238+412=2650，CFBenchmark 140+11=151，与表4一致。不能擅自按标签或模型正确率筛选来凑齐论文数量。

官方只提供英文 FMKG 构建器，本入口暂统一 en；CFBenchmark 的中文图谱主表一致性仍待核实。官方未提供完整评测器，论文未明确全部单位、百分比、精度规则；目前仅保存预测，不用临时宽松匹配器产生主表得分。代码与论文各组件一致性仍需逐项审计，获取官方代码不代表审计完成。

## 复用

```bash
git submodule update --init reproductions/gbfr_dcrc/vendor/gbfr
cd reproductions/gbfr_dcrc
python3.12 -m venv .venv312
.venv312/bin/pip install -r requirements.lock.txt
.venv312/bin/python scripts/audit_data.py
.venv312/bin/python scripts/check_dcrc.py
```

图数据库先按官方 `utils/graph.py` 导入至独立 Neo4j。设置 `GBFR_NEO4J_PASSWORD`、可选 `GBFR_NEO4J_URI`，以及仓库根 `.env` 中 `OPENAI_API_KEY` / `OPENAI_BASE_URL` 后：

```bash
.venv312/bin/python scripts/run_gbfr.py --dataset FinQA --limit 1 --output results/gbfr-finqa-smoke
# 无 --limit 时遍历公开 release；先解决上面的数据版本与评测差异再做正式比较。
```

每次输出含 config、api.jsonl（无请求密钥）、predictions.jsonl。相同输出目录可从已保存样本继续。运行失败与合法拒答必须分开分析。

DCRC `scripts/dcrc_executor.py` 为独立按论文重建的执行器，已验证附录C结果 -0.538；对未接受证据的裸数值、前向引用和非法程序拒绝执行。尚未完整支持表格行聚合和训练奖励，不宣称全部组件完成。训练清单见 `configs/dcrc_training.json`；Kaggle 训练实现将在后续阶段完成。

## 实际运行发现的阻塞（2026-10-30）

Neo4j 5.26 与 Java21 已安装并启动独立实例。官方图谱导入器 `read_nodes()` 在 `item['term_en']` 处抛出 KeyError；源文件共8993条，12条为 error/source 错误对象；8981条含term_en，仅7513个唯一名称，与README宣称7521不一致，且有大量重名记录。详见 `results/graph_audit.json`。已增加可追溯兼容导入：跳过12条明确的生成错误对象，按精确名称合并重复记录，保留公式与代码配对、别名、依赖和类别的并集，定义使用首条。941个名称存在多个定义版本，已记录该选择。未补造缺失术语。此修复属于公开版本的派生图谱，仍有8个术语差异，不能当作原图谱精确复现。**GBFR已完成1条真实API端到端验收，预测94.0；不是主实验准确率。**

GBFR `scripts/run_gbfr.py` 在图谱未满足要求时主动停止，避免官方工作流的“图谱连接失败后降级无图谱”被误算为GBFR。运行器要求实际核验后的7513个术语，并在输出中记录该数量。

## 首条端到端验收

`results/gbfr-finqa-smoke/`：FinQA首条公开样本，gpt-5.6-sol，5次真实API调用，成功输出94.0。见逐样本gold与预测和API原始记录；仅1条，不能推断总体准确率。完整公开release生成入口为 `scripts/run_gbfr_suite.py`，先FinQA，再TAT-QA、FinanceReasoning、CFBenchmark，结果与状态在本目录results中；此流程使用派生图谱和公开版本数据，最终评分仍需口径对齐。
