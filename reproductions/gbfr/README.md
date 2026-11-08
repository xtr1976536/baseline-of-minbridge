> 仓库收录日期：2026-11-08。全量暂停；最新R25为FinQA新10题，预冻结两位/显示精度评分50%/60%，运行后单位解析修正诊断60%/70%；未重新生成预测，尚未达到论文指标。
> 代码、配置、测试、data、runs、research 和 docs 保留交付目录；不重新调用模型。来源包清单仅用于原始交付核对，当前入库清单见仓库发布审计。
> FinanceReasoning轻量包不含权重和索引，按原 bootstrap 脚本重建。临时文件、wheel、超100MB原始归档不入Git；排除清单及哈希见发布审计。

# GBFR 主模型复现

## 最新结果总览

| 数据集与版本 | 样本 | 固定两位准确率 | 参考显示精度准确率 |
| --- | ---: | ---: | ---: |
| FinQA R25，预冻结评分 | 10 | 50% | 60% |
| 同一预测，运行后单位解析修正诊断 | 10 | 60% | 70% |

| R25拒答指标 | 本次结果 |
| --- | ---: |
| 拒答召回 | 1/2（50%） |
| 误拒 | 0/8 |
| 技术错误 | 0 |

全量实验仍暂停，以上仅为10题验证，不与论文全量结果直接比较。运行后诊断只修正评分单位解析，未重新生成预测，原评分保留；TAT-QA本轮未重跑，尚不能宣布达到论文指标。


仅实现论文表 1 的 GBFR 主模型与主实验，不训练权重，不增加基线、消融或其他实验。历史配置保留论文双骨干及四数据集；**当前用户范围是 GPT-5.6 Sol × FinQA / TAT-QA**。

**2026-11-07：全量持续暂停，最新为R25全新FinQA10题验证。** 本轮修复OQA词片段图提示污染及评分单位解析，430项测试通过，仅调用FinQA，TAT-QA未重跑。预先冻结评分为固定两位50%／参考显示精度60%；修复一处“美元/笔交易”的纯评分漏项后，同一冻结预测的运行后诊断为60%／70%，原成绩保留，未重跑模型。拒答召回50%（1/2），误拒0/8，技术错误0，尚未达到论文指标。[最新审计与验证](docs/FINQA_FRESH_R25_20261107.md)明确区分新题、精度政策、运行后评分修正和剩余漏拒。R24及完整40题的历史记录见 [上一轮报告](docs/SMALL_VALIDATION_R24_20261107.md)。旧R19的1,401条记录与断点均保留，小样本未加入全量。图谱仍为公开资产重建，不声称等于作者未公开的最终专家快照。

最新选择、规模、改动原因和验证见 [重建记录](docs/RECONSTRUCTION.md)。原先要求逐项完全一致时的调查保留在 [历史复现记录](docs/REPRODUCTION.md) 和 [历史资产记录](docs/ASSET_RECONCILIATION.md)。

## 准备与检查

需要 Python 3.11+、Git，当前环境为 Windows / Python 3.12。

```powershell
python -m pip install -c requirements.lock.txt -e ".[test]"
python scripts/bootstrap.py --offline
python -m gbfr.cli check --config configs/main.json
python -m pytest -q
```

首次下载时去掉 `--offline`。脚本固定源提交、校验哈希，只读取外部数据；生成图谱、筛选清单、金标修正日志和资产锁。不会调用付费模型，也不运行作者仓库的代码。

主实验资产为 `data/assets/fmkg.reconstructed.json`、`data/main/*.jsonl`，配置为 [configs/main.json](configs/main.json)。原始数据、恢复的历史集合和诊断均另行保留。禁止使用模型预测决定删题或改标签；两种骨干共享同一个资产锁。

```powershell
python scripts/offline_smoke.py
python scripts/validate_main_offline.py
```

这些是模拟协议检查，不产生真实模型准确率。第二条检查全部冻结样本在八个实验单元的保存、分母与续跑，输出仅写入 `tmp/`。

## API 与运行

用户现已指定 **GPT-5.6 Sol**，服务模型 ID 为 `gpt-5.6-sol`，Base URL 为 `https://aiwanwu.cc/v1`。对应 [独立配置](configs/gpt56_sol.json) 使用实际模型名与独立输出目录，不写成论文 GPT-5 的结果。密钥仅在测试进程内使用，未保存到项目文件。

```powershell
$env:GBFR_GPT56_SOL_API_KEY = "你的密钥"
python scripts/api_smoke.py --config configs/gpt56_sol.json
```

该命令调用真实 API，在两个合成例子上验证多跳计算和缺失拒答；结果与正式测试集分开。**当前实验按用户要求暂停，R19入口会受暂停标记拦截；不要恢复旧全量或使用历史四数据集入口启动。** 可用 `python scripts/run_full_r19.py --mode status` 只读查看历史进度。R20离线验证入口为 `python scripts/replay_full_repairs.py --check`，不调用模型。以下 GPT-5 / Qwen3-14B 配置仍保留论文骨干的原始范围。

需要 GPT-5 和 Qwen3-14B 两种模型的服务，各提供 **Base URL、实际模型 ID、API Key**。一个平台同时提供两种模型也可。适配器使用非流式 `/chat/completions`；接口需返回 `choices[0].message.content`。密钥仅从环境变量读取。

```powershell
$env:GBFR_GPT5_API_KEY = "你的密钥"
$env:GBFR_GPT5_BASE_URL = "你的兼容接口地址/v1"
$env:GBFR_QWEN_API_KEY = "你的密钥"
$env:GBFR_QWEN_BASE_URL = "你的兼容接口地址/v1"
```

实际模型 ID 填入配置中的 `backbones.*.model`。服务有并发、QPS/TPM 限制或必填的 thinking/reasoning/token 参数时，一并提供后写入配置；论文未披露的参数会明确记录。当前不擅自添加论文未给出的温度。详细接入说明见 [API 要求](docs/API_REQUIREMENTS.md)。

```powershell
python -m gbfr.cli run --config configs/main.json
```

支持逐题保存和断点续跑，错误记录可用 `run --retry-errors` 重试。模型、端点、参数、源代码、提示词或资产变更时需使用新的 `output_dir`。真实输出写入 `runs/main/`；包括预测、轨迹、用量、指标和 `main_results.md`。错误不计作成功拒答。

由于按论文数值任务要求进行了预先冻结的筛选，部分分母与论文表 4 不同。结果表保留论文参考列并注明该差异，不将两者说成同一测试集合的直接对比。

## 来源

依据用户提供的 [论文](https://aclanthology.org/2026.acl-long.1273/) 和 [作者固定提交](https://github.com/aolaoban/Graph-Bounded_Financial_Reasoning/tree/e1c1704eacfb8a3a522999d4a0ea726189bf5482)。API 格式核对依据 [OpenAI 官方文档](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)。本任务只需要两种骨干的推理服务。
