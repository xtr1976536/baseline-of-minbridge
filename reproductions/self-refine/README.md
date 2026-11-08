> **GSM8K全量已完成：1319题，初始96.2851%，最终96.1334%，累计曾正确97.9530%；改对21、改错23。22题接口失败阶段已补齐，最终0运行错误。详见[结果报告](results/gsm-full-final-20261102/结果报告.md)。其余六任务未完成。**

# Self-Refine复现

## 1. 复现范围与状态

当前阶段：GSM8K数学推理主实验全量已完成并完成两轮发布检查；其余六任务的材料/评测依赖尚未全部验收。范围审计见[主实验范围](docs/主实验范围审计.md)。

[官方论文](https://arxiv.org/abs/2303.17651)；[官方代码](https://github.com/madaan/self-refine)，vendor固定commit9a206d41e5d2d0c241bb441f41eeadb945afaa55。与PoT/Logic-LM环境与结果隔离。

## 2. 复现结果

| 指标 | 正确数 | 准确率 |
| --- | ---: | ---: |
| 初始答案 | 1270/1319 | 96.2851% |
| 最终答案 | 1268/1319 | 96.1334% |
| 累计曾正确 | 1292/1319 | 97.9530% |

改对21题，改错23题，最终净少对2题。22题传输失败已按阶段补齐，成功阶段未重新生成。最终0生成/解析错误。参考论文GPT-4主表为92.9%→93.1%，本次统一gpt-5.6-sol，比较同次初始与最终表现。

- [最终结果与全部证据](results/gsm-full-final-20261102/)：报告、配置、逐题评分与压缩原响应。
- [第一轮发布检查](docs/release-checks/round1.json)、[第二轮干净导出检查](docs/release-checks/round2.json)、[发布清单](docs/release-checks/publication_manifest.json)。
- [返回仓库总览](../../README.md)；[PoT金融结果](../pot/README.md)；[ReAct结果](../../docs/react/README.md)。

## 3. 方法与适配

使用AST加载原Prompt、GSMInit、GSMFeedback与iterative_gsm，保留原方法体及历史更新；替换API transport并去除原整题解析失败自动重试装饰器。初始300token、反馈600token；正文temperature0.7优先于CLI初始默认0；最多4轮，模型反馈出现it is correct提前结束。反馈与改写在同一次调用中返回。

底座统一gpt-5.6-sol；原user prompt不改。Chat的system指令要求Python续写及反馈与函数格式。

### 评分

初始答案准确率、最终答案准确率、作者evaluator的累计any-correct口径分别记录。数值比较来自原check_corr。执行worker隔离临时状态，不继承API密钥，保留错误与全量分母。

## 4. 安装与运行

```bash
git submodule update --init reproductions/self-refine/vendor
cd reproductions/self-refine
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/check_protocol.py
# 付费API，小样本
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_gsm.py --limit 3 --output gsm-smoke-new
# 全量1319题，逐题保存；不同设置使用新目录
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_gsm.py --full --workers 8 --output gsm-full
```

根仓库.env/环境变量提供OPENAI_API_KEY和OPENAI_BASE_URL；不得提交密钥。results保存原提示、响应、程序、每轮评分及配置。官方loop打印prompt的本地log被Git忽略；发布JSON保留调用证据。

早期gsm-smoke为本接入NameError的离线失败（未发API）；gsm-smoke-v2原prompt未适配Chat导致自然语言及parse失败；gsm-smoke-v3为显式格式适配验收，保留各版本而不混合计分。官方upstream README不改写。

## 5. 代码、实验和日志

最终结果以 `results/gsm-full-final-20261102/` 为准：`predictions.jsonl.gz`包含1319题的模型请求/响应、反馈历史、原始程序、执行返回与评分；`scores.jsonl`供快速分析；`transport_failure_records.jsonl.gz`保留22题最初失败；配置、验证、SHA256及报告随附。

`archive/initial_full_run_run_gsm.py`和`archive/resume_run_run_gsm.py`为初次全量和接口续跑的确切源码，SHA256与config吻合，仅作历史审计。当前入口为scripts/run_gsm.py。vendor锁定原作者版本，依赖为requirements.lock.txt。

```bash
# 均不请求API
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/check_protocol.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/summarize_gsm.py --output gsm-full-final-20261102
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_release.py
```

两轮发布检查见docs/release-checks/。不重复上传本机samples/traces、虚拟环境和终端日志：重要调用已汇入压缩轨迹。其余六任务未完成；最终准确率96.1334%，不能以累计97.9530%替代。

## 6. 离线验证

[2026-11-03审计](docs/最终代码一致性审计.md)通过：全部1319题/6014次保存调用经作者原loop离线重建，user提示、历史、解析、停止轮数完全吻合。结论为核心方法与GSM8K主实验的替代底座复现成功；接口与执行环境适配仍按报告披露。检查脚本为scripts/audit_saved_loop.py，不调用API。

发布清单说明：`publication_manifest.json`核对当前Self-Refine文件（不含清单自身所在的检查目录，避免自引用）；`publication_manifest_56aa1ee_historical.json`保留当时发布版本，已去重文件仅在该历史清单中出现。

## 2026-11-08 仓库扩展

仓库现收录七个模型，新增 FinanceReasoning、GBFR、VeriFin。此目录原有结果与范围保持原记录；最新模型范围、结果限制及导航见[仓库总览](../../README.md)。
