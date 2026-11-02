> **2026-11-02更新：接口、执行和评分核查已完成，ConvFinQA已逐ID证实为官方dev421（与论文Test标签不同）。9条多题型API验收已完成，全量未启动。当前设置与限制见[验收与论文一致性](docs/验收与论文一致性.md)，以下早期记录保留供追溯。**

# PoT 主模型复现准备

官方论文：Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks，TMLR 2023，https://arxiv.org/abs/2211.12588v4 。官方代码 https://github.com/TIGER-AI-Lab/Program-of-Thoughts ，submodule固定850399c3eff8c37458a9d642c4a98df287f50f3a。

## 当前范围

先金融三任务：FinQA、ConvFinQA、TAT-QA，few-shot greedy（单条程序）。不训练模型，不运行其他baseline、消融或SC参数扫。当前只允许每任务1..4条验收；没有全量入口。PoT原论文还含数学任务，当前金融设置通过不等于整篇8任务主表复现。

实际底座gpt-5.6-sol，作者参考code-davinci-002；属于替代底座复现。不得用相同模型名称或原论文得分掩盖底座变化。

## 核心流程

scripts/protocol.py使用Python AST提取原run_finqa.py/run_convfinqa.py/run_tatqa.py的完整few-shot字符串和create_reader_request_processed函数，不执行其argparse/main/无限重试。原文空白、拼写（TAT-QA的Quesetion）均保留。FinQA/ConvFinQA4-shot、512输出token；TAT-QA8-shot、256token；temperature=0、top_p=1、n=1、stop双换行，沿用官方。

生成代码不剥离Markdown、不进行答案修复；仅移除响应最前端的边界空白，内部缩进保留。FinQA/ConvFinQA沿用官方&替换、safe_execute、返回值处理和finqa_equal；TAT-QA取ans/units，沿用官方TaTQAEmAndF1。safe_execute在独立子进程中执行、保留原5秒timeout，父进程20秒截止；子进程不继承API密钥。增加AST预检查拒绝明显文件/网络/动态执行调用。该预检查是兼容防护，不是恶意程序的强隔离沙箱，若出现被拦截结果要单独报告，不能算作普通算法错误。

API仅3次上限重试，逐样本失败不丢弃。每次保存prompt/请求参数、原响应及usage、原始代码、执行结果、标准答案、评分、错误和耗时。配置含上游commit与输入SHA256；不同设置不能混写输出目录。

## 已确认的一致性边界

- FinQA公开finqa_test.json：1147题；TAT-QA tatqa_dev.json：1668题。
- ConvFinQA官方脚本读取convfinqa_dev.json：421段对话，评价最后一问；论文Table1标Test421；另有convfinqa_test_turn.json共1521问但不含answer。必须继续与原ConvFinQA数据核对id，不能将dev和test混称。
- 论文最终Table2 greedy参考：FinQA64.5%、ConvFinQA64.6%、TAT-QA69.0%。README另有不同得分，不混用为唯一论文目标。
- 论文SC为temperature0.4/K40，当前仓库为0.5/K30；本阶段不跑SC。
- 作者FinQA/ConvFinQA脚本虽接受start/end，却未实际切片；TAT-QA使用[start:end]，默认end=-1会漏掉最后题。新入口使用明确小样本切片，不重演这些数据覆盖错误。
- parse_api_result使用logprobs排序；greedy只有1条，无排序差异，当前省略logprobs。若扩展SC，必须再审计排序对平票的影响，不能直接沿用本适配。
- Chat不是Completion续写：第一次仅传原prompt，出现代码围栏或自然语言输出，执行失败，记录保留在results/smoke-greedy。第二设置增加Python续写system指令（原user prompt未改），存为独立结果smoke-chat-continuation。该指令是明确的接口适配，不能称prompt完全无变化。
- 新脚本最初误将TAT评分get_overall_metric四个返回值解包为两个，已修正；旧失败记录原样保留，不能把它算成模型错误。

## 使用

```bash
git submodule update --init reproductions/pot/vendor
cd reproductions/pot
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/check_protocol.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_smoke.py --per-task 1 --output smoke-chat-continuation
```

根仓库.env提供OPENAI_API_KEY/OPENAI_BASE_URL；不修改旧实验环境。results/protocol_audit.json包含提示词提取、数据分母、0/False、超时、除零与预检查的验证结果。

尚需：核实ConvFinQA真实split映射，验证更多题型（数字/百分比/布尔/表格span/计数）与作者评分逐样本一致性，确认原stop与token预算在替代模型上能否完整输出，再决定主实验范围。不以3条样本报告完整准确率。

## 2026-11-02 首轮实测

共6次真实API请求（两种接口设置各3题），未全量。第一设置只有原prompt：FinQA/TAT-QA返回代码围栏、ConvFinQA直接自然语言，原执行失败；同时发现并修正新脚本TAT评分四返回值解包问题。

第二设置在system层明确要求Python续写：FinQA首题94.0，对应gold94.0；ConvFinQA首题1.424025457438345，对应gold1.42403，均通过官方比较器。TAT-QA首题程序首行多1空格，原样执行失败；独立results/whitespace_replay.json对同一响应仅lstrip后可执行，作者指标EM=0、F1=0.98（答案漏词），不是正确样本，也不是新请求。早期run_smoke.py保持原样执行；更新版本显式启用边界空白规整，在新acceptance-v2目录验证，旧结果未修改。

离线检查通过：3任务原prompt提取与样本数、0/False、除零/超时、危险调用拒绝。单题成功只说明生成-执行-评分链路可用，不证明整体准确率。
