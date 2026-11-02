# GBFR 主模型复现

> 全量任务已暂停，保留21条修正前诊断预测；小样本默认4条、最多8条。核心审计仍为 NOT_READY，详见 docs/GBFR_CORE_REVIEW.md。

代码、环境与结果独立存放于本目录。

## 当前状态

- GBFR：固定官方仓库 e1c1704eacfb8a3a522999d4a0ea726189bf5482，使用 submodule 保留上游；独立 Python 3.12 环境与独立 Neo4j（Bolt 17687，HTTP 17474）。主流程沿用官方 operators / agents；API transport 从环境读取密钥并记录逐调用原始响应。当前入口只允许1至8条诊断样本；官方图谱导入问题及兼容处理见下文。

## 原文与来源

- GBFR: https://aclanthology.org/2026.acl-long.1273/ ，代码 https://github.com/aolaoban/Graph-Bounded_Financial_Reasoning

## 主实验协议

GBFR 对应 Table 1 的 GBFR 行：FinQA、TAT-QA、FinanceReasoning、CFBenchmark；指标 Total Accuracy 与无答案子集 Abstention Accuracy；参考底座 GPT-5 / Qwen3-14B。当前服务模型 gpt-5.6-sol 为替代底座。


## 已确认的数据和实现差异

详见 `results/data_audit.json`（每文件 SHA256 与样本数）。官方 release：FinQA 1050+97=1147，论文 Table 4 为 1002+97=1099；TAT-QA 1663+151=1814，论文为1119+151=1270。FinanceReasoning 2238+412=2650，CFBenchmark 140+11=151，与表4一致。

官方只提供英文 FMKG 构建器，本入口暂统一 en；CFBenchmark 的中文图谱主表一致性仍待核实。官方未提供完整评测器，论文未明确全部单位、百分比、精度规则；目前仅保存预测，不用临时宽松匹配器产生主表得分。代码与论文各组件一致性仍需逐项审计。

## 复用

```bash
git submodule update --init reproductions/gbfr/vendor/gbfr
cd reproductions/gbfr
python3.12 -m venv .venv312
.venv312/bin/pip install -r requirements.lock.txt
.venv312/bin/python scripts/audit_data.py
```

图数据库先按官方 `utils/graph.py` 导入至独立 Neo4j。设置 `GBFR_NEO4J_PASSWORD`、可选 `GBFR_NEO4J_URI`，以及仓库根 `.env` 中 `OPENAI_API_KEY` / `OPENAI_BASE_URL` 后：

```bash
.venv312/bin/python scripts/run_gbfr.py --dataset FinQA --limit 1 --output results/gbfr-finqa-smoke
# 未指定 --limit 时默认4条，最多8条；正式全量入口已禁用。
```

每次输出含 config、api.jsonl（无请求密钥）、predictions.jsonl。相同输出目录可从已保存样本继续。运行失败与合法拒答必须分开分析。


## 实际运行发现的阻塞（2026-10-30）

Neo4j 5.26 与 Java21 已安装并启动独立实例。官方图谱导入器 `read_nodes()` 在 `item['term_en']` 处抛出 KeyError；源文件共8993条，12条为 error/source 错误对象；8981条含term_en，仅7513个唯一名称，与README宣称7521不一致，且有大量重名记录。详见 `results/graph_audit.json`。已增加可追溯兼容导入：跳过12条明确的生成错误对象，按精确名称合并重复记录，保留公式与代码配对、别名、依赖和类别的并集，定义使用首条。941个名称存在多个定义版本，已记录该选择。未补造缺失术语。此修复属于公开版本的派生图谱，仍有8个术语差异。**GBFR已完成1条真实API端到端验收，预测94.0。**

GBFR `scripts/run_gbfr.py` 在图谱未满足要求时主动停止，避免官方工作流的“图谱连接失败后降级无图谱”被误算为GBFR。运行器要求实际核验后的7513个术语，并在输出中记录该数量。

## 首条端到端验收

`results/gbfr-finqa-smoke/`：FinQA首条公开样本，gpt-5.6-sol，5次真实API调用，成功输出94.0。见逐样本gold与预测和API原始记录。`scripts/run_gbfr_suite.py` 已禁用；已有21条修正前诊断预测保存在results中。修复与核查完成前不恢复全量，最终评分仍需口径对齐。

## 仓库其他已完成实验

[PoT金融三任务](../pot/README.md)已完成全量并通过作者评分复算；[Logic-LM及项目总览](../../README.md)保留既有结果。GBFR继续保持暂停状态。
