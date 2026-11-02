# PoT：金融主模型复现已完成

已完成FinQA、ConvFinQA、TAT-QA共3236题的few-shot greedy全量主实验，逐样本ID/gold核对和作者评分脚本复算均通过。[三数据集报告](results/金融主实验汇总_20261102.md)与[机器可读汇总](results/financial-main-summary-20261102.json)。

| 数据集 | 样本数 | 正确 | 准确率/EM | 论文 | 差值 |
| --- | ---: | ---: | ---: | ---: | ---: |
| FinQA test | 1147 | 857 | 74.7167% | 64.5% | +10.2167 pp |
| ConvFinQA dev最后一问 | 421 | 293 | 69.5962% | 64.6% | +4.9962 pp |
| TAT-QA dev | 1668 | 1249 | 74.8801% | 69.0% | +5.8801 pp |

TAT-QA官方F1：82.8609%。本次采用greedy解码，底座为gpt-5.6-sol；论文底座为code-davinci-002。

## 来源与设置

[论文TMLR 2023](https://arxiv.org/abs/2211.12588v4)；[作者代码](https://github.com/TIGER-AI-Lab/Program-of-Thoughts)，固定commit `850399c3eff8c37458a9d642c4a98df287f50f3a`，保留于vendor子模块。

直接AST提取原prompt与输入builder：FinQA/ConvFinQA 4-shot、512输出token；TAT-QA 8-shot、256输出token；temperature=0、top_p=1、n=1、双换行stop。生成程序调用官方safe_execute、返回值处理及finqa_equal或TaTQAEmAndF1。

API兼容：Chat使用固定Python续写system指令，原user示例与正文保留；仅移除响应最前端空白，不剥Markdown、不修答案。执行worker不继承API密钥，保留5秒执行超时，父进程20秒截止，并有显式AST预检查。修改与历史验收见[一致性说明](docs/验收与论文一致性.md)。

ConvFinQA与原官方data.zip逐ID核验：421条全部是dev，对话和最后标准答案完全一致；详见[划分审计](results/convfinqa_split_audit.json)。

## 结果与审计

- [FinQA完整结果](results/finqa-full-greedy-20261102/)：16并发，857正确，11程序执行失败，0最终运行错误、0截断。
- [ConvFinQA完整结果](results/convfinqa-full-greedy-20261102/)：293正确，6程序失败，0最终运行错误、0截断。
- [TAT-QA完整结果](results/tatqa-full-greedy-20261102/)：1249正确，2程序失败，0最终运行错误、0截断。

各目录包含config、summary、validation、official_format.jsonl、official_scorer.txt、predictions.jsonl、分析与报告。原始模型请求/响应和代码保留于predictions；本机samples断点文件不重复上传。初期smoke与acceptance-v2是历史诊断，不与全量混用。

ConvFinQA/TAT-QA最初同时并发触发429/403，随后单数据集8并发补齐未生成请求；TAT-QA另补齐1次524。只有传输失败重试，已答错或程序失败不重新生成。传输记录压缩归档，详见各目录transport_incident.json。TAT第835题内存tuple与JSON list导致F1差异，最终以发布JSON和作者评分脚本的82.8609%为准，EM不变，审计见score_serialization_audit.json。

## 安装与离线检查

```bash
git submodule update --init reproductions/pot/vendor
cd reproductions/pot
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/check_protocol.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/check_scoring_parity.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_finqa_full.py
# 直接用作者评分脚本检查发布文件（不调用API）
cd vendor/outputs
../../.venv/bin/python compute_score.py --inputs ../../results/finqa-full-greedy-20261102/official_format.jsonl
../../.venv/bin/python compute_score.py --inputs ../../results/convfinqa-full-greedy-20261102/official_format.jsonl
cd ..
../.venv/bin/python compute_score_tatqa.py --inputs ../results/tatqa-full-greedy-20261102/official_format.jsonl
```

## 新生成入口（调用付费API）

根仓库本机.env或环境变量提供OPENAI_API_KEY/OPENAI_BASE_URL；不可提交密钥。小样本run_smoke.py最多每任务4条。全量入口run_finqa_full.py和run_financial_full.py（--task convfinqa或tatqa）固定当前发布目录与设置；已有完整结果无需重跑。需要新模型或新设置时先建立独立输出目录和配置，禁止覆盖发布结果。样本文件已被Git忽略；新克隆应使用发布JSON离线重评，不把缺少本机断点文件误判为未完成并直接调用API。

代码、环境和结果存放于本目录。返回[项目总览](../../README.md)。
