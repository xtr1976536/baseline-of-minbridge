> 仓库收录日期：2026-11-08。Hard 238题，217题正确，91.18%；论文表5为91.60%。替代骨干 gpt-5.6-sol，未运行同骨干无增强对照。
> 代码、配置、测试、data、runs、research 和 docs 保留交付目录；不重新调用模型。来源包清单仅用于原始交付核对，当前入库清单见仓库发布审计。
> FinanceReasoning轻量包不含权重和索引，按原 bootstrap 脚本重建。临时文件、wheel、超100MB原始归档不入Git；排除清单及哈希见发布审计。

# FinanceReasoning 表 5 最佳方法复现

**executor-v3 全量运行已完成：217/238，准确率 91.18%；程序或执行失败 0，筛选格式失败 0，未解决接口错误 0。105 项测试通过。** [最新结果与审计](docs/RESULTS.md)及[执行器最小修复](docs/EXECUTOR_V3.md)。

**上一轮 IDs-v2：212/238，准确率 89.08%；筛选格式失败 0，接口错误 0。75 项测试通过。** [该轮结果](docs/RESULTS_IDS_V2.md)与[最小修改及公平性记录](docs/SELECTOR_IDS_V2.md)。上一轮为 159/238（66.81%），旧结果保留。

按本次用户选择，仅实现论文 §4.3 / 表 5 的最佳 GPT-4o 知识增强方法：**LLM-Instructed Function Retrieval + LLM as Judge + PoT**。Hard 子集全部 238 题，函数库全部 3,133 条。没有训练、其他骨干、基线、消融或 Reasoner + Programmer 实验。

代码与数据置于独立目录，不依赖或改动旁边的 GBFR / VeriFin 项目。**论文 GPT-4o 骨干实验未运行；用户于 2026-11-06 指定改用 `gpt-5.6-sol`，该替换骨干的真实实验已完成。论文 91.60% 只是 GPT-4o 参考值。**

2026-11-06 本机验证：41 项测试通过；完整 Contriever 索引已构建，全部函数描述未截断；真实检索与全部 238 题的协议保存/续跑检查通过，再次运行新增阶段调用为 0。验证记录在 `research/final_validation.json` 和 `research/offline_validation.json`。

上一轮 labels-v1 的真实 API 接入与执行修正：55 项测试通过，`https://aiwanwu.cc/v1` 的 Chat Completions 接口已返回 `gpt-5.6-sol`；全部 238 题已完成，最终 159 题正确，准确率 66.81%；62 题筛选格式失败计错，接口故障为 0。当前默认启动配置已指向 `configs/local.aiwanwu-gpt56sol-executor-v3.json`，旧结果为 `runs/aiwanwu-gpt56sol-final/`，接入记录为 `research/aiwanwu_integration.json`。密钥用 Windows 当前用户 DPAPI 加密保存在项目外，启动器仅向本次 Python 子进程传入环境变量。

```powershell
.\scripts\run_aiwanwu.ps1
# 只对接口故障进行恢复：
.\scripts\run_aiwanwu.ps1 -RetryErrors
```

此运行复现同一知识增强方法，但使用用户指定的不同骨干；不能称为相同模型的论文数值复现。下文 GPT-4o 配置仍作为论文原设置保留。

## 方法

1. 配置指定的骨干根据原问题及完整上下文生成检索查询。本轮为 `gpt-5.6-sol`，论文原骨干为 `gpt-4o-2024-11-20`。
2. 本地 `facebook/contriever-msmarco` 检索函数描述，精确内积搜索取前 30 个函数。
3. 同一个骨干按原相关性标准筛选 30 个带固定编号的候选，返回最多 3 个入选编号；全无用时允许空知识。
4. 同一个骨干根据原问题、上下文和筛选函数生成 `solution()`，独立 Python 进程执行并返回单一数值或布尔值。题目明确要求百分数时，可解析完整百分数字符串而不缩放数值；支持标准数学类 `NormalDist`。
5. 数值比较：`abs(pred - gold) <= abs(gold) * 0.002`；零标签要求精确零，3 个原生布尔标签要求类型及值都匹配。不通过变号、乘除 100 或改变金额尺度补救答案。

查询和 PoT 采用作者固定提交的原模板；candidate-ids-v2 保留筛选的原金融相关性标准，仅改变候选编号及输出契约，六条源模板仍原样保存在 prompts.json；模型输入只有原问题、上下文与参考函数，没有金标、标准解、难度统计或测试题来源。14 个空上下文问题保持原样，它们自身已含题干信息。

## 安装与准备

Python 3.11+，当前验证环境为 Windows / Python 3.12，CPU 即可运行检索。下列命令在本目录执行：

```powershell
python -m pip install -c requirements.lock.txt -e ".[test]"
python scripts/bootstrap.py
python -m fr_repro check
python -m pytest -q
python scripts/offline_validate.py
```

已下载过全部固定资产时，可使用 `python scripts/bootstrap.py --offline`。首次准备下载约 438 MB 公开 Contriever 权重并构建全部函数索引，无需 Hugging Face Token 或 embedding API。固定数据版本、模型版本、哈希和身份清单写入 `data/assets.lock.json`；实际索引写入 `data/index/`。

`offline_validate.py` 使用真实 Contriever 检查检索，再用明确的协议替身验证全部 238 题的调度、保存与续跑。这不能产生真实模型性能。

## API 与正式运行

仅需 **GPT-4o 一种文本推理 API**。优先提供论文快照 `gpt-4o-2024-11-20`，三阶段共用该模型。所需服务信息见 [API 要求](docs/API_REQUIREMENTS.md)。

```powershell
$env:FR_GPT4O_API_KEY = "你的密钥"
$env:FR_GPT4O_BASE_URL = "https://你的接口地址/v1"
python -m fr_repro run --limit 2
python -m fr_repro run
```

首次两题只是接入检查，之后续跑原实验，不另抽样或丢弃检查题。实际服务模型 ID 填入 `configs/main.json`。如需平台专用配置，复制为 `configs/local.main.json` 并传入 `--config configs/local.main.json`。`.env.example` 仅说明环境变量，不会自动加载。

完整实验约 **714 次成功文本调用（238 × 3）**，不含接口层重试。支持逐题原子保存与中断续跑；`--retry-errors` 只重试接口错误，成功的阶段从缓存恢复。无模型自我修复、金标反馈、重试挑选最佳答案或执行失败后的直接数值猜测。

输出在 `runs/main/`：逐题预测、生成查询、30 个检索 ID/得分、最多 3 个选中函数、三阶段原始响应、生成程序、执行状态、用量、模型返回信息、指标和结果表。API Key 不进入输出。模型输出格式错误、代码无效或执行失败算错；API 故障和未完成题目使结果表保持 `pending`。完整分母固定为 238，不能仅统计成功题。

源代码、提示词、数据、检索方式、依赖版本、API 地址、模型 ID 或参数变化时，必须指定新的 `output_dir`，不能把不同实验混进旧结果。两份进程不能同时写同一实验目录。函数索引设置或编码实现变化时须在新 `data_dir` 重新准备索引。

详见 [复现选择和改动依据](docs/REPRODUCTION.md)。
