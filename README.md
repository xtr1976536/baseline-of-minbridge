# MinBridge Baselines

Logic-LM 与 ReAct 复现仓库。作者代码以固定 Git 子模块保存，原始许可证保留。**最终 Logic-LM 配置已经确定：作者原解释器 + 原始程序 prompt 前置 26 词格式约束 + CoT 答案去 Markdown 后交给作者评分器。** 不使用本项目曾试验的查询修复解释器。

## 已完成结果

ProofWriter 完整 600 题已重新生成并完成评测，无 self-refinement：

| 指标 | 本次 GPT-5.6 替代底座 | 论文 GPT-4 |
|---|---:|---:|
| 总体准确率 | 79.83%（479/600） | 79.66% |
| 程序可执行率 | 100%（600/600） | 99.0% |
| 可执行样本准确率 | 79.83% | 79.6% |
| 独立 CoT 准确率（本次先去 Markdown） | 68.67%（412/600） | 68.11% |

本轮没有使用 CoT 回退。未去 Markdown 的 CoT 原评分为 35%，两种分数都保留。Markdown 清理属于明确披露的格式兼容处理；不根据推理内容猜答案。结果见 `reports/proofwriter-final-summary.json` 和逐题 `reports/proofwriter-final-predictions.json`。不是“除了底座外零改动”的严格复现，也不据此宣称其他四数据集已经验证成功。

## 安装

```bash
git clone --recurse-submodules https://github.com/xtr1976536/baseline-of-minbridge.git
cd baseline-of-minbridge
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python -r requirements.lock.txt
export PATH="$PWD/.venv/bin:$PATH"
bash scripts/apply_runtime_patches.sh
bash scripts/build_prover9.sh   # FOLIO 需要；需系统 C 编译器
cp .env.example .env
# 在本机填写 OPENAI_API_KEY 和 OPENAI_BASE_URL，不提交 .env。
```

环境变量优先于本机 `.env`。密钥不进入命令参数、Git 或 API 日志；请求仅保存提示词和非敏感参数。供应商 usage 与请求预算的差异记为警告，保留原文，不按用量统计丢弃答案或反复生成。`tiktoken` 为可选诊断工具，并不决定评分。

## 最终主实验入口

```bash
# 先冻结 5 道题配置，不调用 API
.venv/bin/python scripts/run_logic_experiment.py --dataset FOLIO --limit 5 --prepare-only

# 全新小规模测试：作者原 dev.json；程序和 CoT 均新生成
.venv/bin/python scripts/run_logic_experiment.py --dataset ProntoQA --limit 10
.venv/bin/python scripts/run_logic_experiment.py --dataset FOLIO --limit 10
.venv/bin/python scripts/run_logic_experiment.py --dataset LogicalDeduction --limit 10
.venv/bin/python scripts/run_logic_experiment.py --dataset AR-LSAT --limit 10

# 完整数据：省略 --limit。默认模型 gpt-5.6-sol，最多 4 并发
.venv/bin/python scripts/run_logic_experiment.py --dataset ProofWriter

# 显式断点续跑：模型、数据选择和源文件指纹必须相同
.venv/bin/python scripts/run_logic_experiment.py --dataset FOLIO --limit 10 \
  --resume results/<该次运行目录> --workers 1

# 已完成最终运行的本地重评测，不调用模型
.venv/bin/python scripts/evaluate_logic_experiment.py --run results/<该次运行目录>
```

程序始终使用作者各数据集模板，AR-LSAT 用 GPT-4 对应的 `AR-LSAT-long.txt`；只统一前置下面这段原封不动的约束，不增加新示例或改作者逻辑内容：

> For the final problem, output only the plain-text logic program, following the example's exact headings and syntax. No Markdown, blank lines within sections, or additional explanation.

CoT prompt 不改。先按作者 `The correct option is:` 分割，再去掉加粗、反引号、围栏、标题/列表等显示标记，最后使用原作者 `evaluate_QA`。不能将自然语言中任意 A/B/C 当答案，也不根据 gold 修正输出。程序成功执行即使用求解器结果，答错也不回退；仅解析、执行或映射失败才使用同 ID 的清理后 CoT。额外的异常回退会明确记录。

无 self-refinement 的主表是当前唯一主实验；不自动进入其他任务或运行付费重试纠错。

## 输出、审计与两轮检查

每次运行创建新目录；不自动读“最新缓存”。每条记录原子保存请求和输出，避免中断时只保存一半；失败停止派发，保存其他在途成功响应，显式续跑只补缺失 ID。目录包括 `run.json`、`program/records/`、`cot/records/`、原始响应快照、`summary.json`、`predictions.json`、`report.md`。程序运行期间 records 是断点真源；聚合快照在阶段结束时写出。

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s scripts -p 'test_*offline.py' -v
.venv/bin/python scripts/audit_core_protocol.py
```

发布的两轮检查见 `docs/final-release-checks.md`。下一步先在本机对其余四数据集小规模测试，再决定全量；本次整理未发起新的付费生成，也没有设置自动定时任务。

## 历史与其他工作

旧的多版本 Logic-LM 生成/推理/修复入口、长格式约束与探索性解释器已从当前代码树移除，Git 历史可追溯。本机旧脚本另存于仓库外的历史目录，实验原始响应/日志仍留在本机，默认不上传。不要从历史文件推断当前状态。

ReAct 入口 `scripts/run_react.py`、环境脚本与 GBFR 独立工作保持原样，未混入本次 Logic-LM 最终发布；对应数据准备见既有文档。它们的历史结果不代表本次已完成端到端复现。

## 来源

- Logic-LM，Findings of EMNLP 2023：https://aclanthology.org/2023.findings-emnlp.248/
- 作者代码：https://github.com/teacherpeterpan/Logic-LLM
- ReAct：https://github.com/ysymyth/ReAct
