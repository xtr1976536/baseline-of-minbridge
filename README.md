# baseline of minbridge

ReAct 与 Logic-LM 主模型复现。仓库记录 benchmark、配置、脚本、结果、文献与日志；所有本项目说明使用中文。官方代码以固定 Git 子模块引用，保留原文及许可证。

**当前状态：准备与作者程序重放。用户将在最后提供 API；尚未完成端到端主实验，不宣称复现成功。**

## 目录

- `upstream/`：官方代码和 benchmark，固定 commit；克隆请加 `--recurse-submodules`。
- `scripts/`：ReAct 主模型执行、Logic-LM 逻辑程序生成、CoT 回退生成、求解评测与 self-refinement、审计脚本。
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
scripts/build_prover9.sh
```

密钥通过环境变量提供；参考 `.env.example`，不要提交配置密钥。提供替代模型时，结果必须标为替代底座，不与原模型表格混写。

## ReAct

```bash
.venv/bin/python scripts/run_react.py --task hotpotqa --prepare-only
.venv/bin/python scripts/run_react.py --task hotpotqa --model text-davinci-002 --limit 500
.venv/bin/python scripts/run_react.py --task fever --model text-davinci-002 --limit 500
```

作者 ReAct 代码用 `text-davinci-002` Completion。若 API 服务要求 Chat 接口，可指定 `--api-mode chat`，并将结果标记为替代接口/底座复现；实际服务模型以 `--model` 记录，原作者模型标签以 `--reference-model` 记录。ALFWorld/WebShop 入口也已提供，但各自环境必须另行验收。

## Logic-LM

```bash
.venv/bin/python scripts/replay_logic.py --dataset ProntoQA
.venv/bin/python scripts/run_logic.py --dataset ProntoQA --split test --model gpt-4
.venv/bin/python scripts/run_logic_cot.py --dataset ProntoQA --split test --model gpt-4
.venv/bin/python scripts/run_logic_inference.py --dataset ProntoQA --split test --model gpt-4 \
  --programs results/<逻辑程序文件>.json --cot results/<CoT回退文件>.json
.venv/bin/python scripts/run_logic_refinement.py --dataset AR-LSAT --split test --model gpt-4 \
  --programs results/<首轮程序文件>.json
```

生成新的逻辑程序后，生成对应 CoT 预测，并调用作者求解器；求解失败时逐样本采用对应 CoT 答案。self-refinement 按作者方案只运行 AR-LSAT 与 FOLIO，默认最多三轮，每轮对失败程序重新调用模型。生成、回退、推理和修正脚本都保留官方数据、提示模板、stop、温度与 token 设置。首条只重放作者缓存，不能标成重新调用 GPT-4。

FOLIO 所用 Prover9 编译产物置于被忽略的 `.local/Prover9`，不会改动官方子模块内源文件或二进制。

替代 API 的设置示例：`OPENAI_BASE_URL` 与 `OPENAI_API_KEY` 在本机环境变量中设置；`--api-model <服务商模型ID>` 指定实际调用模型，`--model gpt-4` 保留 Logic-LM 作者模型标签与 GPT-4 专用提示选择。实际模型不同于参考模型时，结果必须标记为替代底座复现。API 密钥不进入参数、不写日志。

## 已知限制

论文原用模型已从 OpenAI API 下线，端到端 API 运行尚未开始。ReAct 的 Wikipedia 与 WebShop 网络端点目前不可达。Logic-LM 推理与 self-refinement 流程脚本已补全，待接入 API 后执行全量；作者缓存重放见 `docs/当前结果.md`，不视为模型生成复现。所有环境失败保留日志，每项结果写明真实完成范围。

## 文献

- ReAct，ICLR 2023：https://arxiv.org/abs/2210.03629
- Logic-LM，Findings of EMNLP 2023：https://aclanthology.org/2023.findings-emnlp.248/
- 官方 ReAct：https://github.com/ysymyth/ReAct
- 官方 Logic-LM：https://github.com/teacherpeterpan/Logic-LLM

## 大型环境数据

ALFWorld 已在本机通过 `alfworld-download` 下载；134 个 unseen 游戏已完成 reset 检查。数据安装在 ALFWorld 自身缓存目录，不将数百 MB 环境资源直接镜像到 GitHub；克隆后运行相同下载命令，并核对日志中的版本和任务数。
