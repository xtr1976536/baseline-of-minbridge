> **2026-11-02：3题GSM8K验收完成，原始/最终均3/3，0解析或运行错误；仅为小样本。1319题GSM8K全量已启动，8并发，结果目录results/gsm-full-20261102。其他六任务尚未完成，不能称整篇论文复现结束。**

# Self-Refine复现

当前阶段：先复现GSM8K数学推理主实验，再逐项解决其余六任务的材料/评测依赖。**尚未完成整个七任务论文复现**。范围审计见[主实验范围](docs/主实验范围审计.md)。

[官方论文](https://arxiv.org/abs/2303.17651)；[官方代码](https://github.com/madaan/self-refine)，vendor固定commit9a206d41e5d2d0c241bb441f41eeadb945afaa55。与PoT/Logic-LM/GBFR环境与结果隔离。

## GSM方法

不是凭描述重写循环：使用AST加载原Prompt、GSMInit、GSMFeedback与iterative_gsm，保留原方法体及历史更新；替换API transport并去除原整题解析失败自动重试装饰器。初始300token、反馈600token；正文temperature0.7优先于CLI初始默认0；最多4轮，模型反馈出现it is correct提前结束。反馈与改写在同一次调用中返回。

底座统一gpt-5.6-sol；原user prompt不改。Chat的system指令仅要求Python续写/反馈+函数格式，不引入新证据、标准答案、正确性判断或执行错误反馈。

## 评分

初始答案准确率、最终答案准确率、作者evaluator的累计any-correct口径分别记录；不可把any-correct当最终答案。数值比较来自原check_corr。执行worker隔离临时状态，不继承API密钥，保留错误与全量分母。未增加工具反馈给模型。

## 安装与运行

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
