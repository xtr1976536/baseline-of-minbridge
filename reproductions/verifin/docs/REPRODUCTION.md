# 复现依据与改动说明

当前修正版已按用户后续指令完成 FinanceBench 67 题全量，使用同一 GPT-5.6 Sol 接口，未运行其他实验。结果及与旧版、论文 Table 4 的对比见 `runs/financebench-revised-v1/comparison.md`：精度 79.17%、决策准确率 80.00%、覆盖率 49.25%，FA=5、Abs=34、错误/遗漏=0。代码与通过 54 项测试的小样本版本相同，运行期间未变更；33 份判定证明重放一致。修正依据与此前 12 题对照见 [PILOT_FIXES.md](PILOT_FIXES.md)。下文旧 67 题指标与 39 项测试均为上一版本历史记录，未被覆盖。

## 范围与版本

本任务是 VeriFin，用户已明确确认。附件 SHA-256：`07dea58bcf91be05d310116040d062139d1f5196dd4bbc4619d7bec0e4214f16`，共 9 页，arXiv v3。用户进一步授权只使用 1–2 个金融数值推理数据集，并明确指定 GPT-5.6 Sol。本次完整运行 FinanceBench（67）；XBRLFiling（600）已准备而未启动推理。选择 FinanceBench 优先的最低完成范围在推理前记录；最终只跑一个集合以控制 CPU 时间和 API 用量，未按题目结果筛选。当前默认配置仅包含 FinanceBench。不实施 repair、基线或消融。样本身份在预测前固定，不按运行结果增删。原论文六骨干配置单独保存在 `configs/paper-backbones.json`，不与当前用户指定骨干的结果混合。

作者源码固定到 `5c49943e8aa43f3dc03c1b2058a73469b22c5c5e`。保留其模型提示词、问题分解、答案生成、候选数值解析、事实抽取、注册表和 XML 解析工具；没有直接运行默认实验 CLI。新增薄运行层修正论文冲突，主程序不读取历史预测来构造答案或选择样本。

## 按论文实现的必要改动

| 论文 | 公开默认实现的差异 | 本实现 |
|---|---|---|
| §3.2，式 1 | CLI 默认 oracle evidence；检索默认 dense | 文档内 role-expanded 检索，余弦加标签词法得分，cross-encoder 重排；FinanceBench 使用原始完整 PDF |
| §4.1，图 3 | 全文检索可能重新暴露 XBRLFiling 被遮盖的目标 | XBRLFiling 的输入文档采用官方 redacted statement；不把未遮盖原文或金标公式给答案生成器 |
| §3.3–3.5 | `resolve_policy_formula` 根据与候选值的距离选公式变体 | 问题运算→linkbase→注册表→披露等式依次授权；以结构、单位、角色消歧，未决则拒答 |
| §3.5 | 文本抽取可能在缺 XBRL 时继续成为决策事实 | 每个操作数必须绑定指定财报的概念、期间、单位、值、accession、fact ID；注册表绑定忽略抽取值，启发式才做 plausibility 检查 |
| §3.5 | companyfacts 回退可能跨 filing/重述版本 | 只绑定已经下载并固定的该 filing XML；同期间冲突值不任选一个 |
| §3.6 | 默认可让 LLM 生成 SMT；原代码容差含候选答案精度和 0.1% 相对下限 | 按公式编译精确有理数约束；容差来自问题/披露精度，没有候选相对误差下限 |
| §3.3、§4.3 | 默认允许一次候选差异驱动的 UNSAT fact retry | 正式主实验不修复答案、不基于候选改抽事实；候选数值最后才进入约束 |
| §4.2 | 默认摘要与论文 TA/FA/TR/FR 口径不同 | 单独评测原候选正确性；未决正确性不计 precision/accuracy，仍计 coverage；完整 N 不变 |

只生成确定的算术约束，不执行 LLM 生成的 Python 或 SMT 程序。支持四则运算、固定整数幂、abs/min/max、CAGR 的正实根代数编码和 registry coverage_ratio；除零和不存在的公式域返回 Abstain。无法授权的形式不由参数知识补造。

## 输入与评测隔离

模型输入只显式读取问题、允许的文档文本和公开定义。Gold、参考计算、reference operands、facts 标签、derivation、block_mapping、人工正确性审查及历史结果不传入生成/验证函数。XBRLFiling 只从 source provenance 中白名单读取公开财报身份，用于下载对应原始文件，不把其 reference 计算作为公式来源。

公式与事实在解析候选前固定。Registry 有多个不等价可用公式且不能凭问题/单位消歧时拒答，不选最接近候选的版本。常规绑定按声明概念顺序选择，记录源 fact；重复同值事实可合并，冲突值拒答。符号标签启发式使用最少多余 token 的唯一匹配，并要求其与独立抽取值在同号、三倍范围内。三倍阈值沿用公开代码，论文未给出具体阈值。

## 无法原样还原的资产与工程约定

1. **TAT-DQA（已移出正式范围）**：以下仅保留为先前准备的历史审计，不参与当前准备、检查、运行、资产锁或报告。附件提到该集合，但源码、发布文件及数据卡没有该最终集合和对应 filings。已下载官方 `next-tat/TAT-DQA@bc46208b22f0bfe47152c98fd0938d238ce868c2` 测试 gold、完整 PDF 和 OCR JSON。固定采用官方 test split 是本次复现假设。统一保留单个数值标签，再按来源公司/年度唯一定位 SEC 10-K；不截前 403 条，也不按模型结果筛选。无法定位的来源明确排除，所有模型使用同一冻结集合；规模和选择身份不等同于论文 403。若日后获得原索引，可单独开新输出目录运行原集合。
2. **注册表**：实际公开文件为 58 个 metric policies、61 个 semantic concepts；附件为 59、126，并提到 17 项 operation rules。不能凭计数编造缺失条目。本实现保留公开来源定义和已有运算实现，覆盖不足正常拒答，差异保留。
3. **公开源缓存**：作者不发布原始 XML/linkbase/companyfacts/PDF 冻结缓存。依 accession 重新获取不可变 filing XML、calculation 与 label linkbase，保存 URL 与 SHA-256；无法取得原作者缓存哈希相同性，因此不声称与其缓存完全一致。FinanceBench 非 XBRL 可用文档和无计算定义的任务继续保留在 N 中，不用 gold evidence 回填。
4. **检索参数**：论文未给出 K、lambda、chunk size、精确模型快照。本机无 CUDA，正式预测前固定使用 `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` 与 `cross-encoder/ms-marco-MiniLM-L6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`；仍执行密集余弦加词法匹配及交叉编码器重排。K=10、first-stage=30、lambda=0.2、200 词块、40 词重叠。以上均为预测前固定的工程约定，没有依据评测答案选型或调参。FinanceBench 不通过 gold 页码补充 corpus。
5. **财报精度**：问题明确的舍入精度优先；直接提取可用 XBRL decimals，派生货币量可用文档披露的 display scale。未在财报中披露的派生比例没有唯一“最后一位”，统一取两位小数、半单位容差 0.005，并在每题标记为复现假设；不从候选字符串推断精度。
6. **模型设置**：按用户指定，所有 LLM 阶段统一使用 AIwanwu 的 `gpt-5.6-sol`，服务返回同名模型标识。沿用论文 GPT-5.5 的 low、8192 tokens、无 temperature 设置，并保留作者提示词。planner、extractor 与 answer 使用同一骨干，是沿用源代码的约定。该骨干变更不能视为原论文六骨干数值的精确复现；服务标识也不等于独立验证了供应商底层权重。
7. **评测**：只解析参考标签中可唯一确定的数值及显式单位，不任意选择多个数字之一。允许明确的单金额或单百分数句子；含多个候选目标或单位未明的标签保留为 correctness unresolved，不能据此虚增正确率。评测容差按标签精度定义，与验证容差分开。报告保留未决数量、ERROR 和未完成数。

这些差异由公开资产缺口决定，可能改变覆盖率和与论文数值的可比性。代码能执行完整协议，不代表可以仅靠 API 精确复原未发布的实验资产。

准备阶段另外识别出 HTML 错误页伪装成 PDF 的旧链接，已替换为同一 accession 的正式 SEC HTML 并保存原响应；两份有读取警告的 TAT-DQA 文档使用官方完整 OCR blocks，不使用 gold block_mapping。XBRLFiling 的 29 条参考操作数残差另存 `research/xbrl_reference_residuals.json`；没有改变原标签或将其误解释为模型误差。

准备阶段冻结集合为 **XBRLFiling 600 / FinanceBench 67**，本次正式运行仅 FinanceBench 67。以下第三数据集信息仅为历史准备记录，不属于当前正式实验：TAT-DQA 的 477 条来自 57 个可唯一匹配的年度 SEC filing，保留全部通过预定规则的数值题，未截取成 403。重建过程不使用模型预测。

仅影响已排除的 TAT-DQA 历史资料：Nordic American Tankers 2019 的原始 instance 已恢复，包含 767 个数值事实；其 calculation 文件、带 download query 的重试及官方 XBRL ZIP 均持续返回 503。已明确保留这份原始 instance，并记录 calculation/label 获取缺口；只允许其他独立授权来源，无法授权时拒答，不编造 linkbase、不移除该发行人的问题。详细轨迹见 `research/optional_source_gaps.json`。两份独立 earnings PDF 没有发布的 XBRL instance，保留在 FinanceBench 分母中并记录事实源限制。

## 检查与产物

主实验 preflight 检查数据身份和哈希、原始财报与 corpus、冻结锁。锁文件只表示输入固定，不是论文一致性证书。模型 API key、base URL 在所有请求前检查；代码/参数/资产/有效接口变化不能续写旧实验。

`research/reproduction-tests.xml` 保存新增测试结果。测试覆盖原论文配置的 12 单元串行/并发运行及续跑、用户指定骨干范围识别、未选集合不参与报告和资产锁、候选独立性、完整指标分母、正确/错误/缺事实三种路径、真实 XML 解析、单位/期间/重复冲突、CAGR 与除零、Z3 核和 standalone replay、缓存内容身份以及截断响应。

`research/offline_smoke.json` 使用实际 SEC Apple XBRL、脚本化 LLM 响应。它不是正式数据集上的真实模型性能。源仓库的全套历史测试包含本任务不使用的 consensus、旧 counterexample 求解器等路径；它们的失败不会被记作本地新增主路径测试通过。

最终主实验输出位于 `runs/gpt56-sol-final/`，67 条全部完成，错误与遗漏均为 0。原始完整推理保留于 `runs/gpt56-sol-v3/`。39 项测试通过；28 份接受/拒绝 SMT 证明全部独立重放一致。首批执行发现的显示单位重复换算已修正；旧部分输出和修正前代码保留，重叠候选答案从缓存复用，记录见 `research/implementation_versions/unit_scale_fix.json`。

结束后修正参考标签显式单位的优先级：问题单位启发式会把 “separation” 误识别为 “ratio”，故唯一参考金额明确写出 billion/million 时优先采用该单位；没有单位规模的金额仍继承问题声明。所有 67 条重新统一计分，正确性标签与指标均未变化，原答案、判定、检索、事实和证明均不变，也未产生新的推理请求。完整审计见 `research/implementation_versions/final_scoring_audit.json`。

本次严格原始标签计分得到 TA=18、FA=6、TR=1、FR=1、Abs=39、正确性未决=2；接受精度 75.00%、决策准确率 73.08%、覆盖率 41.79%。本次没有复现论文的零误接受结论。6 次 FA 中有 5 次是原始 XBRL 数值与带 `.00` 的参考金额之间小于 0.5 百万美元的舍入差异，另 1 次为 Pepsi 重组费用 0 与参考 411 百万美元不符。上述 FA 全部保留；没有修改原始金标或放宽计分容差。详细案例见 `research/main_error_cases.json`。所有来源恢复、排除、下载失败及已获取文件状态均可在 `research/` 审查。

样本间并发数为 4，所有 LLM 请求合计最多 4 个并发；CPU 检索与 Z3 分别串行保护。每题仍按原有阶段执行，最终日志按固定样本顺序写入，续跑不会重复记数。并发变更前的输出保留在 `runs/gpt56-sol-v2/`，原始候选继续复用同一缓存。
