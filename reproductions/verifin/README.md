> 仓库收录日期：2026-11-08。FinanceBench 67题；本地主舍入接受精度100%、决策准确率100%、覆盖率67.16%。1条未决排除在常规准确率分母外，按错误计97.78%；严格口径80%/81.82%/67.16%。覆盖率未达70.1%，本地舍入规则非作者官方阈值。
> 代码、配置、测试、data、runs、research 和 docs 保留交付目录；不重新调用模型。来源包清单仅用于原始交付核对，当前入库清单见仓库发布审计。
> FinanceReasoning轻量包不含权重和索引，按原 bootstrap 脚本重建。临时文件、wheel、超100MB原始归档不入Git；排除清单及哈希见发布审计。

# VeriFin 主模型主实验复现

本次已按用户授权完成 **FinanceBench 全部 67 题**，仅使用原 GPT-5.6 Sol 接口。35 条验证记录原样复用，补跑其余 32 题；代码、输入、评分规则与 35 题版本一致。主舍入口径下接受精度 **100%**、决策准确率 **100%**、覆盖率 **67.16%**；覆盖率低于论文的 70.1%，**仍不能判为全部达标**，需要至少再有 2 题具备有效判定。相对上一修正版全量的同口径 100%、96.67%、49.25%，覆盖率提高 17.91 个百分点。

主计数 TA=40、FA=0、TR=4、FR=0、弃答=22、正确性未决=1。未决题不计入常规准确率分母；将它保守地计作错误，决策准确率为 **97.78%**。旧严格显示精度口径完整保留，结果为 **80%、81.82%、67.16%**，也未全部达标。本地主舍入规则不是作者公布的官方数值阈值。运行错误与遗漏均为 0，另有 1 条非 JSON 输出被当前解析器归为弃答，不能据此声称没有格式失败。

45 份 SMT、原始事实身份及独立算术重放一致；语义复核另外发现 1 条未决税率拒绝存在重复百分比换算。它没有被算作正确拒绝，也没有在全量结束后修改判定或标签。全部问题、8 条舍入差异与逐题记录见 [全量对比报告](runs/financebench-full-post35-v1/comparison.md)、[语义及格式复核](runs/financebench-full-post35-v1/response_review.json)、[完整性审计](runs/financebench-full-post35-v1/validation.json)。本轮没有运行其他数据集、骨干、baseline、repair、训练或追加采样。

本轮配置为 `configs/financebench-full-post35.json`，输出目录为 `runs/financebench-full-post35-v1/`。同一命令只会读取已完成记录并续跑未完成项；当前已无未完成项。

```powershell
python scripts/run_main.py run --config configs/financebench-full-post35.json --datasets FinanceBench
```

## 上一轮固定 35 题验证

上一轮已完成**固定 35 题**验证：按运行前声明的本地 FinanceBench 舍入规则，接受精度 **100%**、决策准确率 **100%**、覆盖率 **82.86%**，均达到论文 GPT-5.5 的三项数值门槛。修改前相同 35 题按同一规则为 100%、95.65%、65.71%；6 题从弃答恢复，弃答 12→6。TA=27、FA=0、TR=2、FR=0，错误和遗漏均为 0。

**评分区别必须保留：**原 FinanceBench 采用允许微小舍入的人工评审，未公开统一数值阈值；本轮本地操作化不是作者官方阈值。旧严格显示小数位口径仍为 **81.48%、82.76%、82.86%**，未全部达到门槛。两种规则在正式运行前固定，所有金标不改；5 条金额格式/舍入差异完整披露，评分修正不算模型收益。见 [35题完整对比](runs/validation35-v1/comparison.md)、[修订与评分依据](docs/VALIDATION35_FIXES.md)。84 项测试通过，29 份 SMT 以及独立原事实/算术检查一致。**当时尚未启动新的 67 题全量。**

## 上一轮固定 50 题历史记录

已完成**固定 50 题的两轮端到端验证和一次同候选、同证据重验**。最终版本 v3：接受精度 **77.78%**、决策准确率 **76.67%**、覆盖率 **62%**；修改前同 50 题分别为 78.95%、79.17%、52%。覆盖率提高 10 个百分点，但正确性指标未达标，**尚不能判为修改成功**。TA=21、FA=6、TR=2、FR=1、弃答=19、正确性未决=1；运行错误和遗漏均为 0，31 份 SMT 重放一致，70 项回归测试通过。

所有版本和严格计分均保留，没有启动新的 67 题全量。最终配置为 `configs/coverage50-v3.json`，同候选重验使用 `python scripts/reverify_coverage50.py`，不生成答案；与第二轮 50 个候选和证据的逐题哈希核对一致。见 [最终对比报告](runs/coverage50-v3/coverage_report.md)、[修改与各轮记录](docs/COVERAGE50_FIXES.md)。门槛仍为接受精度 100%、决策准确率 ≥86.7%、覆盖率 ≥70.1% 且无错误与遗漏。

## 上一轮修正版 67 题历史记录

上一轮修正版已按用户授权完成 **FinanceBench 全部 67 题主实验**，仅使用同一个 GPT-5.6 Sol 接口。与修改前相比：接受精度 75.00%→79.17%，决策准确率 73.08%→80.00%，覆盖率 41.79%→49.25%，误接受 6→5，弃答 39→34。运行错误与遗漏均为 0，33 份判定 SMT 证明重放一致。

新结果位于 `runs/financebench-revised-v1/`，配置为 `configs/financebench-revised.json`。67 题候选答案、检索计划和检索片段与旧版完全一致，旧结果及原始标签未改。见 [完整对比与论文差距](runs/financebench-revised-v1/comparison.md)、[主结果与置信区间](runs/financebench-revised-v1/main_results.md)。没有运行其他数据集、其他骨干、基线、repair、消融或训练。

```powershell
python scripts/run_main.py run --config configs/financebench-revised.json --datasets FinanceBench
```

本次使用与已通过 54 项测试的小样本版本完全相同的代码，全量期间未改代码。原 Pepsi 概念误绑已改为正确拒绝，没有新增 FA/FR；但 1 条旧正确接受因英文定义 `less` 未被解析而变成弃答。剩余 5 次 FA 均为原有金额舍入差异，本次仍未复现论文的零误接受结论。此前 12 题小样本及修正依据见 [PILOT_FIXES.md](docs/PILOT_FIXES.md)。小样本配置仍禁止启动全量。

## 上一版本完整主实验记录

本目录针对用户提供的 **2608.10213v3.pdf（VeriFin）**，沿用 GBFR 对话的复现要求：论文优先、只做主模型主实验、按必要性尽量少改、不根据预测结果修改数据。与父目录中的 GBFR 实现分开存放。

当前按用户明确指定使用 **GPT-5.6 Sol** 作为 VeriFin 的单一骨干，已完成 **FinanceBench 公开数值子集全部 67 题**。用户允许只做 1–2 个集合，本次正式配置固定为 FinanceBench；XBRLFiling 的 600 题及资产已准备，未启动推理。原论文六骨干配置保存在 `configs/paper-backbones.json`。不运行 TAT-DQA、基线、修复实验、消融或训练。

**真实主实验已结束，39 项测试通过，28 份接受/拒绝 SMT 证明重放一致，运行错误和遗漏均为 0。** 严格原始标签计分：接受精度 75.00%，决策准确率 73.08%，覆盖率 41.79%；TA=18、FA=6、TR=1、FR=1、弃答=39、正确性未决=2。本次没有复现论文的零误接受结论。见 [结果与置信区间](runs/gpt56-sol-final/main_results.md)、[计分与差异说明](runs/gpt56-sol-final/EXPERIMENT_NOTES.md)。作者原版未公开完整 v3 资产，且本次骨干由用户另行指定，因此不能声称原始实验资产或数值完全等价。详情见 [复现说明](docs/REPRODUCTION.md) 和 [API 清单](docs/API_REQUIREMENTS.md)。

## 安装和准备

需要 Python 3.11+、Git。已经下载的原始文件会复用。建议新建独立环境。

```powershell
python scripts/bootstrap.py
python -m pip install -c requirements.lock.txt -e ./upstream
python -m pip install -c requirements.lock.txt -e .
python -m pip install -c requirements.lock.txt pytest
python -m vf_repro.runner prepare
```

固定作者源码提交 `5c49943e8aa43f3dc03c1b2058a73469b22c5c5e`。`upstream/` 保留作者源码，新增逻辑位于 `src/vf_repro/`。作者的历史结果只用作资料，不会混入本地结果表。

下载 SEC 原始财报前设置 `SEC_USER_AGENT` 为项目名称和联系人邮箱。它用于公开财报下载，不是付费模型 API。用户已在本聊天提供联系邮箱；命令示例不重复展示个人信息。

```powershell
$env:SEC_USER_AGENT = "VeriFin research 联系邮箱"
python -m vf_repro.runner discover-financebench
python -m vf_repro.runner prepare
python -m vf_repro.runner download-documents
python -m vf_repro.runner download-filings
python -m vf_repro.runner check
```

`prepare` 按配置准备所选集合；当前为 FinanceBench。之前准备的 XBRLFiling 与 TAT-DQA 资料保留，但不参与当前正式运行或报告。资产检查只核对所选集合及对应财报；已有资产锁中也保留了准备阶段冻结的 XBRLFiling 哈希。

## 验证

```powershell
python -m pytest -q
python scripts/offline_smoke.py
```

测试覆盖原论文六骨干配置的 12 个运行单元、串行/并发续跑和当前单骨干范围识别，使用脚本响应与测试财报；另一个离线脚本使用实际下载的 Apple XBRL，验证论文图 3 的正确、错误、缺失操作数三种情况。它们不是真实 LLM 评测。

## 接入 API 和运行

填写 [API 清单](docs/API_REQUIREMENTS.md) 中对应的环境变量，并核对 `configs/main.json` 内服务实际使用的 model ID。`.env.example` 仅作字段说明，不会自动读取；密钥不写入 JSON、日志或结果文件。

```powershell
python -m vf_repro.runner lock
python scripts/run_main.py run --datasets FinanceBench
```

一次服务一个开放权重模型时，可以分组运行，可使用原配置完成所选范围的 12 组（当前用户指定的单骨干运行不需要此步骤）：

```powershell
python -m vf_repro.runner run --config configs/paper-backbones.json --models Qwen2.5-7B
python -m vf_repro.runner report
```

当前 `run` 默认只运行 FinanceBench；同一配置续跑会复用已完成的 67 条记录。若未来另行运行 XBRLFiling，需要新的配置和输出目录，不能混入本次结果。

重跑相同命令自动续跑。重试接口/解析错误用 `--retry-errors`；已成功生成的候选答案通过请求缓存复用，不为获得更好结果重采样。代码、参数、接口或资产发生变化后需要新 `output_dir`，不同设置不能混跑。

每组保存逐题预测、原始答案、检索轨迹、公式来源、XBRL 事实身份、SMT、冲突核心和指标。`runs/gpt56-sol-final/main_results.md` 只显示本地实测。错误、模型拒答、未决正确性及未完成样本分别统计，完整分母保留。

首批真实请求发现了注册表显示单位换算与操作数单位归一化重复的问题，已修正并增加测试。旧输出保留在 `runs/gpt56-sol/`，修正后使用新的输出目录；已有候选答案使用请求缓存复用，不重新采样。变更记录见 `research/implementation_versions/unit_scale_fix.json`。

完整推理原记录保留在 `runs/gpt56-sol-v3/`。结束后修正了参考答案显式单位与问题单位启发式的优先级，再对全部 67 条统一计分；本次计分结果没有变化，未重新调用模型。最终配置与结果位于 `runs/gpt56-sol-final/`，审计见 `research/implementation_versions/final_scoring_audit.json`。

## 来源

- [VeriFin v3](https://arxiv.org/abs/2608.10213v3)，实现内容依据本次用户附件。
- [作者发布仓库](https://github.com/verifiedfinance/anon/tree/5c49943e8aa43f3dc03c1b2058a73469b22c5c5e)。
- [XBRLFiling 官方数据集](https://huggingface.co/datasets/bethelhall/XBRLFiling)。
- [TAT-DQA 官方数据](https://huggingface.co/datasets/next-tat/TAT-DQA)。

当前本机无 CUDA，检索使用固定版本 `BAAI/bge-small-en-v1.5` 与 `cross-encoder/ms-marco-MiniLM-L6-v2`；仍执行密集余弦＋词法匹配与交叉编码器重排。该配置在正式预测前固定，不以评测答案选型。

样本间并发数为 4，所有 LLM 请求合计最多 4 个并发；CPU 检索与 Z3 分别串行保护。每题仍按原有阶段执行，最终日志按固定样本顺序写入，续跑不会重复记数。并发变更前的输出保留在 `runs/gpt56-sol-v2/`，原始候选继续复用同一缓存。
