# baseline of minbridge

ReAct 与 Logic-LM 主模型复现。仓库记录 benchmark、配置、脚本、结果、文献与日志；所有本项目说明使用中文。官方代码以固定 Git 子模块引用，保留原文及许可证。

**当前状态：准备与作者程序重放。用户将在最后提供 API；尚未完成端到端主实验，不宣称复现成功。**

## 目录

- `upstream/`：官方代码和 benchmark，固定 commit；克隆请加 `--recurse-submodules`。
- `scripts/`：ReAct 主模型执行、Logic-LM 生成及求解重放、审计脚本。
- `configs/`：从作者 notebook 提取的 ReAct 主模型定义，不执行其他 baseline。
- `results/`：实际运行的逐样本记录与汇总，作者缓存重放和 API 输出分开。
- `logs/`：运行、依赖及环境检查日志。
- `docs/实验协议.md`：原论文主表、指标、差异与限制。
- `references/`：论文原文、文本与来源。
- `manifests/`：数据校验和、上游版本和运行环境。

## 环境

```bash
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python -r requirements.lock.txt
export PATH="$PWD/.venv/bin:$PATH"
```

密钥通过环境变量提供；参考 `.env.example`，不要提交配置密钥。提供替代模型时，结果必须标为替代底座，不与原模型表格混写。

## ReAct

```bash
.venv/bin/python scripts/run_react.py --task hotpotqa --prepare-only
.venv/bin/python scripts/run_react.py --task hotpotqa --model text-davinci-002 --limit 500
.venv/bin/python scripts/run_react.py --task fever --model text-davinci-002 --limit 500
```

`--api-mode chat` 仅用于兼容替代服务，不属于原 Completion 接口设置。ALFWorld/WebShop 入口也已提供，但各自环境必须另行验收。

## Logic-LM

```bash
.venv/bin/python scripts/replay_logic.py --dataset ProntoQA
.venv/bin/python scripts/run_logic.py --dataset ProntoQA --model gpt-4
```

第二条生成新的程序文件，随后按脚本输出的路径执行求解。首条只重放作者缓存，不能标成重新调用 GPT-4。

## 已知限制

论文环境包含已变化的模型接口、网页与旧求解器依赖。当前本机 Prover9 需原生编译，作者附带 Linux 二进制不能直接运行。所有环境失败保留日志。详细结果见 `docs/当前结果.md`，每项结果写明真实完成范围。

## 文献

- ReAct，ICLR 2023：https://arxiv.org/abs/2210.03629
- Logic-LM，Findings of EMNLP 2023：https://aclanthology.org/2023.findings-emnlp.248/
- 官方 ReAct：https://github.com/ysymyth/ReAct
- 官方 Logic-LM：https://github.com/teacherpeterpan/Logic-LLM

## 大型环境数据

ALFWorld 已在本机通过 `alfworld-download` 下载；134 个 unseen 游戏已完成 reset 检查。数据安装在 ALFWorld 自身缓存目录，不将数百 MB 环境资源直接镜像到 GitHub；克隆后运行相同下载命令，并核对日志中的版本和任务数。
