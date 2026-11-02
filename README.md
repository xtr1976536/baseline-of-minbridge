# MinBridge：推理模型复现与评估

本仓库保存相互隔离的论文复现代码、逐样本输出与评测证据。当前 **Logic-LM 主实验、PoT 金融三数据集主实验、Self-Refine GSM8K主实验均已完成**；ReAct 的 HotpotQA 500题验证已完成（EM49.20%、F1 64.90%）；GBFR 保留并暂停正式全量，继续核心一致性核查。

Self-Refine 的 GSM8K 1319题主实验已完成：初始96.2851%，最终96.1334%；自反馈改对21题、改错23题，净少对2题。[完整结果](reproductions/self-refine/results/gsm-full-final-20261102/结果报告.md)及[两轮发布检查](reproductions/self-refine/docs/release-checks/)已上传。其余六任务尚未完成。

## 项目与结果入口

| 项目 | 当前状态 | 入口 |
| --- | --- | --- |
| Logic-LM | 五数据集全量主实验完成 | 下方完整结果；[最终实验](experiments/final/)与[报告](reports/) |
| PoT | 金融三数据集全量完成，作者评分脚本复核通过 | [代码与使用](reproductions/pot/README.md)、[三数据集结果](reproductions/pot/results/金融主实验汇总_20261102.md) |
| Self-Refine | GSM8K 1319题完成；最终96.1334% | [代码与说明](reproductions/self-refine/README.md)、[结果报告](reproductions/self-refine/results/gsm-full-final-20261102/结果报告.md) |
| ReAct | HotpotQA 500题完成；EM49.20%、F1 64.90% | [最终代码与说明](docs/react/README.md)、[实验与日志](experiments/react/hotpotqa/) |
| GBFR | 保留；全量暂停，核心审计 NOT_READY | [GBFR说明](reproductions/gbfr/README.md) |

## Self-Refine：GSM8K主实验最终结果

| 指标 | 正确数 | 比例 |
| --- | ---: | ---: |
| 初始答案 | 1270/1319 | 96.2851% |
| 最终答案（主指标） | 1268/1319 | 96.1334% |
| 作者脚本累计曾正确 | 1292/1319 | 97.9530% |

自反馈改对21题、改错23题，净下降0.1516个百分点；累计曾正确不是最终答案准确率。底座gpt-5.6-sol；论文GPT-4行92.9%→93.1%。22题HTTP403失败阶段已补齐，1297题首轮成功轨迹保持不变，28个已成功阶段响应复用。最终0未解决生成/解析错误；两轮发布检查通过。范围为GSM8K数学推理，不包含其余六任务或金融适配评估。

[原始压缩轨迹、逐题评分与配置](reproductions/self-refine/results/gsm-full-final-20261102/) · [方法和运行入口](reproductions/self-refine/README.md)。

## ReAct：HotpotQA 复现结果

| 数据集 | 样本数 | 正确数 | 本次 EM | 论文 GPT-3 EM | 论文 PaLM-540B EM | 本次 F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HotpotQA dev | 500 | 246 | **49.20%** | 30.8% | 27.4% | **64.90%** |

本次使用 gpt-5.6-sol，4 个独立进程并行题目，题内顺序执行。论文 GPT-3 数值来自附录 Table 5，PaLM-540B 数值来自正文 Table 1 的纯 ReAct 行。题单采用作者随机种子 233；全部 EM/F1 已用作者评分函数复算。运行配置、逐题轨迹和日志见 [ReAct 实验目录](experiments/react/hotpotqa/)，命令见 [ReAct README](docs/react/README.md)。

## PoT：金融主实验最终结果

| 数据集 | 样本数 | 正确数 | 本次准确率/EM | 论文Table 2 greedy | 差值 |
| --- | ---: | ---: | ---: | ---: | ---: |
| FinQA test | 1147 | 857 | 74.7167% | 64.5% | +10.2167个百分点 |
| ConvFinQA dev，最后一问 | 421 | 293 | 69.5962% | 64.6% | +4.9962个百分点 |
| TAT-QA dev | 1668 | 1249 | 74.8801% | 69.0% | +5.8801个百分点 |

TAT-QA F1为82.8609%。共3236题，采用gpt-5.6-sol替代原Codex；ConvFinQA按作者代码实际使用dev421，论文Test标签差异已有逐ID核验。失败计入完整分母，三个结果均通过作者评分脚本复算。

PoT独立放在`reproductions/pot/`，不共用或覆盖Logic-LM/ReAct/GBFR环境与结果。完整请求/响应、程序、标准答案、评分、配置、失败记录与验证见其results目录。项目安装和重评命令见各自README；下方保留Logic-LM完整发布说明。

---

# Logic-LM：已完成的主实验

五个数据集的全量主实验及 LogicalDeduction 独立 CoT 全量实验已完成。底座为服务商声明的 `gpt-5.6-sol`，参考论文为 Logic-LM（GPT-4、Table 2，无 self-refinement）。**作者原求解器与评分器保持不变；数据集格式约束和 LogicalDeduction 的小兼容处理均公开记录。**

## 最终结果

| 数据集 | 样本 | 主准确率 | 论文 | 可执行率 | 论文 | Exe_Acc | 论文 | CoT | 论文 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ProofWriter | 600 | 79.83% | 79.66% | 100% | 99.0% | 79.83% | 79.6% | 68.67% | 68.11% |
| ProntoQA | 500 | 99.40% | 83.20% | 100% | 100% | 99.40% | 83.2% | 83.60% | 98.79% |
| FOLIO | 204 | 76.47% | 78.92% | 77.45% | 79.9% | 79.75% | 80.4% | 66.18% | 70.58% |
| LogicalDeduction | 300 | **99.33%¹** | 87.63% | 98.33% | 100% | 99.32% | 87.6% | **98.33%²** | 75.25% |
| AR-LSAT | 231 | 68.83% | 43.04% | 52.38% | 32.6% | 67.77% | 60.0% | 67.97% | 35.06% |

¹ LogicalDeduction 最小程序格式修正后的原主实验为 **295/300（98.33%）**。最终代码加入已确认的 CoT 显式选项提取，对**原配套 CoT**本地重评后额外识别对3条回退答案，得到 **298/300（99.33%）**。两个版本均保存。

² 此列为后来**独立重新生成的300条 CoT**：295/300（98.33%）。同批答案仅去 Markdown 的分数为50.67%。主实验配套旧CoT经最新提取也为295/300，但两者是不同批次。

FOLIO/AR-LSAT 的执行时间限制会受机器负载影响。本次发布保留原完成时冻结成绩；附带的当前代码离线复验中，FOLIO主准确率仍为156/204，但一条超时状态变化使可执行率成为159/204，而原记录为158/204。`recorded-*` 与 `current-policy-*` 均保留，不覆盖原记录。

AR-LSAT作者附录/README写230，而公开评测文件实际231条，本项目保留全部231条。

## 目录：只保留最终入口和最终实验

- `scripts/run_logic_experiment.py`：五数据集新主实验，程序＋配套CoT，各自记录，4并发，原子断点。
- `scripts/evaluate_logic_experiment.py`：作者求解器、回退、作者评分器；原始/适配分数都保留。
- `scripts/run_ld_cot_full.py`：仅LogicalDeduction独立300条CoT，不生成程序。
- `scripts/logical_deduction_compat.py`：只整理段落标题布局和 `(A)`→`A)`；不改语句、数值和顺序；不从多个程序中挑一个。
- `scripts/logical_deduction_cot.py`：仅该数据集的明确选项提取；多个候选、越界或无显式选项时弃权，绝不读取gold推断答案。
- `configs/prompts/`：三个数据集类别的额外格式约束；作者正文/示例不改。
- **`experiments/final/`**：五个主实验及LD独立CoT的原始输出、压缩请求/响应、运行配置、日志、逐题预测、冻结指标和当前代码重评。`index.json` 指定唯一最终版本。
- `reports/`：汇总表、3970条请求完整性核验、SHA256清单及两轮验收日志。
- `docs/`：最终方法差异、结果解释和发布检查。
- `upstream/`、`patches/`：固定作者子模块及可复现运行时补丁。

旧调参脚本、旧Logic-LM缓存重放成绩和过时说明已从当前版本移除；Git历史仍可追溯。本机保留旧实验原始数据，各项目的代码与结果分别存放。

## 安装

```bash
git clone --recurse-submodules https://github.com/xtr1976536/baseline-of-minbridge.git
cd baseline-of-minbridge
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python -r requirements.lock.txt
export PATH="$PWD/.venv/bin:$PATH"
bash scripts/apply_runtime_patches.sh
bash scripts/build_prover9.sh  # FOLIO需要本机C编译器
cp .env.example .env
# 在本机填写密钥和端点。已有环境变量优先于.env；密钥不得提交。
```

并发只用于模型生成；本地作者求解器使用固定缓存文件，**不要同时评测同一个数据集的两个运行**。有网络失败时停止派发、保存已经返回的在途结果，显式续跑只补缺失项。

## 运行新实验（会调用付费API）

```bash
# 不调用API，只保存一份小样本配置
.venv/bin/python scripts/run_logic_experiment.py --dataset FOLIO --limit 10 --prepare-only

# 全量；默认gpt-5.6-sol、单条user消息、温度0、top_p=1、max_tokens=1024、stop=------
.venv/bin/python scripts/run_logic_experiment.py --dataset LogicalDeduction --workers 4
# 其他选择：ProofWriter / ProntoQA / FOLIO / AR-LSAT；加--limit 10可小测

# 续跑必须使用同一个数据集、模型和样本选择；不自动复用“最新缓存”
.venv/bin/python scripts/run_logic_experiment.py --dataset LogicalDeduction \
  --resume results/<本次运行目录> --workers 4

# 仅LogicalDeduction独立CoT
.venv/bin/python scripts/run_ld_cot_full.py
.venv/bin/python scripts/run_ld_cot_full.py --resume results/<该次CoT目录>
```

主表实验不做self-refinement，不因答错或格式失败而再次生成。模型成功求解但答错仍采用作者答案；只有失败时按ID回退到对应CoT。LogicalDeduction显式提取只是后处理，不改CoT prompt和推理过程；其余数据集只做Markdown清理。

## 不调用API的检查和重评

```bash
# 核对3970个发布请求、样本、原始响应、提取结果和分数，以及敏感信息
.venv/bin/python scripts/verify_final_release.py
# 重新调用本地作者求解器，结果写.local，不覆盖发布成绩
.venv/bin/python scripts/replay_final_release.py --dataset LogicalDeduction
# 测试和作者源码一致性检查
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s scripts -p 'test_*offline.py' -v
.venv/bin/python scripts/audit_core_protocol.py
```

`*.json.gz`/`*.jsonl.gz`采用标准gzip以减少重复prompt占用空间，Python `gzip`或`gzip -dc`即可读取。依赖安装外的上述检查不发送模型请求。`summary.json`是发布成绩，`recorded-summary.json`是原运行冻结成绩，`current-policy-summary.json`是最新代码的离线复验。请求日志没有Authorization headers；本机路径已脱敏，响应内容和提示词不改。

## 运行适配

- 原提示词逐字保留，前置约束分别适配通用逻辑程序、CSP、Z3 DSL；原求解器源码未修改。
- FOLIO只配置Prover9路径；AR-LSAT子进程屏蔽会混入答案的Z3弃用UserWarning，不修改Z3推理逻辑。
- 供应商usage不是独立分词测量；异常保留原文并记录。本次部分AR-LSAT回答经独立诊断分词也超过请求1024，上限实际执行无法认证；原始输出和请求参数均保存在日志中。
- 中途网络/额度故障和恢复记录随最终实验保存；没有将失败请求当成模型答错。ProofWriter一次初期拒收响应丢失原文的审计缺口也在日志中披露。

来源：[Logic-LM论文](https://aclanthology.org/2023.findings-emnlp.248/)；[作者代码](https://github.com/teacherpeterpan/Logic-LLM)；[ReAct](https://github.com/ysymyth/ReAct)。
