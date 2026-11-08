# MinBridge：七个推理模型复现

本仓库统一整理 Logic-LM、ReAct、PoT、Self-Refine、FinanceReasoning、GBFR、VeriFin。底座统一使用 `gpt-5.6-sol`，原论文模型见各模型说明。

## Logic-LM

**范围与状态：** 五个逻辑数据集主实验完成。

| 数据集 | 样本 | 本次准确率 | 论文参考 |
| --- | ---: | ---: | ---: |
| ProofWriter | 600 | 79.83% | 79.66% |
| ProntoQA | 500 | 99.40% | 83.20% |
| FOLIO | 204 | 76.47% | 78.92% |
| LogicalDeduction | 300 | 99.33% | 87.63% |
| AR-LSAT | 231 | 68.83% | 43.04% |

**代码、实验和日志：** [模型README](docs/logic-lm/README.md) · [实验结果与证据](experiments/final/)。

## ReAct

**范围与状态：** HotpotQA dev 500题完成。

| 数据集 | 样本 | 本次EM | 本次F1 | 论文GPT-3 EM | 论文PaLM EM |
| --- | ---: | ---: | ---: | ---: | ---: |
| HotpotQA dev | 500 | 49.20% | 64.90% | 30.8% | 27.4% |

**代码、实验和日志：** [模型README](docs/react/README.md) · [实验结果与证据](experiments/react/hotpotqa/)。

## PoT

**范围与状态：** 金融三数据集3236题完成。

| 数据集 | 样本 | 本次准确率/EM | 论文准确率 |
| --- | ---: | ---: | ---: |
| FinQA test | 1147 | 74.7167% | 64.5% |
| ConvFinQA dev最后一问 | 421 | 69.5962% | 64.6% |
| TAT-QA dev | 1668 | 74.8801% | 69.0% |

TAT-QA F1为82.8609%。ConvFinQA沿用作者代码实际dev划分，论文Test标签差异已有审计。

**代码、实验和日志：** [模型README](reproductions/pot/README.md) · [实验结果与证据](reproductions/pot/results/)。

## Self-Refine

**范围与状态：** GSM8K 1319题完成。

| 指标 | 正确/总数 | 本次 | 论文GPT-4 |
| --- | ---: | ---: | ---: |
| 初始答案 | 1270/1319 | 96.2851% | 92.9% |
| 最终答案 | 1268/1319 | 96.1334% | 93.1% |
| 累计曾正确 | 1292/1319 | 97.9530% | 不作最终答案比较 |

改对21题、改错23题，净少对2题。其余六任务未完成。

**代码、实验和日志：** [模型README](reproductions/self-refine/README.md) · [实验结果与证据](reproductions/self-refine/results/gsm-full-final-20261102/)。

## FinanceReasoning

**范围与状态：** Hard 238题主方法实验完成。

| 数据集 | 样本 | 正确 | 本次准确率 | 论文表5 |
| --- | ---: | ---: | ---: | ---: |
| FinanceReasoning Hard | 238 | 217 | 91.18% | 91.60% |

本次底座为 `gpt-5.6-sol`，论文底座为 `gpt-4o-2024-11-20`。

**代码、实验和日志：** [模型README](reproductions/finance-reasoning/README.md) · [数据集](reproductions/finance-reasoning/data/) · [实验结果与证据](reproductions/finance-reasoning/runs/aiwanwu-gpt56sol-executor-v3/)。

## GBFR

**范围与状态：** 全量暂停，最新完成R25 FinQA新10题验证。

| 数据集与版本 | 样本 | 固定两位准确率 | 参考显示精度准确率 |
| --- | ---: | ---: | ---: |
| FinQA R25，预冻结评分 | 10 | 50% | 60% |
| 同一预测，运行后单位解析修正诊断 | 10 | 60% | 70% |

| R25拒答指标 | 本次结果 |
| --- | ---: |
| 拒答召回 | 1/2（50%） |
| 误拒 | 0/8 |
| 技术错误 | 0 |

修正诊断使用同一批预测，仅调整评分器的单位解析。

**代码、实验和日志：** [模型README](reproductions/gbfr/README.md) · [数据集](reproductions/gbfr/data/) · [实验结果与证据](reproductions/gbfr/runs/)。

## VeriFin

**范围与状态：** FinanceBench 67题完成，覆盖率尚未达标。

| 数据集 | 样本 | 评分口径 | 接受精度 | 决策准确率 | 覆盖率 |
| --- | ---: | --- | ---: | ---: | ---: |
| FinanceBench | 67 | 本地主舍入 | 100% | 100% | 67.16% |
| 论文参考 | — | 论文GPT-5.5 | 100% | 86.7% | 70.1% |

本次底座为 `gpt-5.6-sol`，本地主舍入规则并非作者公布的官方数值阈值。1条正确性未决不计入常规准确率分母，按错误计入时决策准确率为97.78%。

**代码、实验和日志：** [模型README](reproductions/verifin/README.md) · [数据集](reproductions/verifin/data/) · [实验结果与证据](reproductions/verifin/runs/financebench-full-post35-v1/)。

## 仓库结构与发布检查

- `docs/logic-lm/`、`docs/react/`：两模型完整说明；其代码保留在根scripts及upstream。
- `reproductions/pot/`、`reproductions/self-refine/`：独立代码、环境与结果。
- `reproductions/finance-reasoning/`、`reproductions/gbfr/`、`reproductions/verifin/`：新增三模型代码、数据、日志及结果。
- `experiments/`、`reports/`：Logic-LM/ReAct冻结实验与日志。
- [配置说明](configs/README.md)、[文献说明](references/README.md)。
- [三轮整理检查](docs/release-audit-20261104/README.md)。

新增资料收录范围与两轮上传后核查见[发布审计](docs/release-audit-20261108/README.md)。
