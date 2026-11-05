# MinBridge：四个推理模型复现

本仓库统一整理 Logic-LM、ReAct、PoT、Self-Refine。使用服务商声明的 `gpt-5.6-sol` 作为替代底座，原模型及必要适配在各模型说明中披露。以下完成状态仅限列出的主实验范围，不代表各论文全部任务。

## Logic-LM

**范围与状态：** 五个逻辑数据集主实验完成。

| 数据集 | 样本 | 本次准确率 | 论文参考 |
| --- | ---: | ---: | ---: |
| ProofWriter | 600 | 79.83% | 79.66% |
| ProntoQA | 500 | 99.40% | 83.20% |
| FOLIO | 204 | 76.47% | 78.92% |
| LogicalDeduction | 300 | 99.33% | 87.63% |
| AR-LSAT | 231 | 68.83% | 43.04% |

**方法与适配：** 见[完整说明](docs/logic-lm/README.md)，保留作者核心流程，明确消息格式、执行环境和后处理差异。

**代码、实验和日志：** [模型README](docs/logic-lm/README.md) · [实验结果与证据](experiments/final/)。

**运行与验证：** README均提供安装、生成与离线核验入口；发布结果保留，不为贴近论文分数调参。

## ReAct

**范围与状态：** HotpotQA dev 500题完成。

| 数据集 | 样本 | 本次EM | 本次F1 | 论文GPT-3 EM | 论文PaLM EM |
| --- | ---: | ---: | ---: | ---: | ---: |
| HotpotQA dev | 500 | 49.20% | 64.90% | 30.8% | 27.4% |

**方法与适配：** 见[完整说明](docs/react/README.md)，保留作者核心流程，明确消息格式、执行环境和后处理差异。

**代码、实验和日志：** [模型README](docs/react/README.md) · [实验结果与证据](experiments/react/hotpotqa/)。

**运行与验证：** README均提供安装、生成与离线核验入口；发布结果保留，不为贴近论文分数调参。

## PoT

**范围与状态：** 金融三数据集3236题完成。

| 数据集 | 样本 | 本次准确率/EM | 论文准确率 |
| --- | ---: | ---: | ---: |
| FinQA test | 1147 | 74.7167% | 64.5% |
| ConvFinQA dev最后一问 | 421 | 69.5962% | 64.6% |
| TAT-QA dev | 1668 | 74.8801% | 69.0% |

TAT-QA F1为82.8609%。ConvFinQA沿用作者代码实际dev划分，论文Test标签差异已有审计。

**方法与适配：** 见[完整说明](reproductions/pot/README.md)，保留作者核心流程，明确消息格式、执行环境和后处理差异。

**代码、实验和日志：** [模型README](reproductions/pot/README.md) · [实验结果与证据](reproductions/pot/results/)。

**运行与验证：** README均提供安装、生成与离线核验入口；发布结果保留，不为贴近论文分数调参。

## Self-Refine

**范围与状态：** GSM8K 1319题完成。

| 指标 | 正确/总数 | 本次 | 论文GPT-4 |
| --- | ---: | ---: | ---: |
| 初始答案 | 1270/1319 | 96.2851% | 92.9% |
| 最终答案 | 1268/1319 | 96.1334% | 93.1% |
| 累计曾正确 | 1292/1319 | 97.9530% | 不作最终答案比较 |

改对21题、改错23题，净少对2题。其余六任务未完成。

**方法与适配：** 见[完整说明](reproductions/self-refine/README.md)，保留作者核心流程，明确消息格式、执行环境和后处理差异。

**代码、实验和日志：** [模型README](reproductions/self-refine/README.md) · [实验结果与证据](reproductions/self-refine/results/gsm-full-final-20261102/)。

**运行与验证：** README均提供安装、生成与离线核验入口；发布结果保留，不为贴近论文分数调参。

## 仓库结构与发布检查

- `docs/logic-lm/`、`docs/react/`：两模型完整说明；其代码保留在根scripts及upstream。
- `reproductions/pot/`、`reproductions/self-refine/`：独立代码、环境与结果。
- `experiments/`、`reports/`：Logic-LM/ReAct冻结实验与日志。
- [配置说明](configs/README.md)、[文献说明](references/README.md)。
- [三轮整理检查](docs/release-audit-20261104/README.md)。

第三方子模块README保留作者原文；项目自有说明使用统一完成范围与指标口径。已有实验的逐题内容和冻结指标不因目录整理而更改。
