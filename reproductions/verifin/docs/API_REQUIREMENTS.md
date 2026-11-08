# 当前已接入的接口

修正版全量已完成，实际配置为 `configs/financebench-revised.json`，输出 `runs/financebench-revised-v1/`。它继续使用下述同一模型与服务，未新增其他实验接口。

用户已指定 `gpt-5.6-sol`，当前配置通过 `https://aiwanwu.cc/v1` 调用此单一骨干，不再要求补齐六个原论文骨干 API。原配置保存在 `configs/paper-backbones.json`。密钥使用 Windows DPAPI 加密存放于项目外，通过 `python scripts/run_main.py run --datasets FinanceBench` 在进程内加载。

本次已完成 FinanceBench 全集 67 题；XBRLFiling 已准备而未运行。当前正式配置只包含 FinanceBench。用户提供的这一套接口已经足够，无需补充其他模型 API。所有结果以 GPT-5.6 Sol 标识，不冒充原论文骨干结果。

下列清单为原论文骨干的可选配置参考，当前运行不依赖它们。

# 原论文六骨干的可选接口参考

以下仅供未来另行运行原论文六骨干时参考；当前用户指定的 GPT-5.6 Sol 实验不需要这些额外接口。

每个服务提供 **API key、base URL、实际 model ID、可用并发/限流**。同一个供应商可同时提供多个模型，无需为每个模型分别开户。密钥使用本地环境变量；不要写进源码或公开文件。

| 论文中的模型 | 接口 | 密钥变量 | 接口地址变量 |
|---|---|---|---|
| GPT-5.5 | OpenAI Chat Completions | `VF_OPENAI_API_KEY` | `VF_OPENAI_BASE_URL` |
| Claude Haiku 4.5 | Anthropic Messages；兼容网关也可调整配置 | `VF_ANTHROPIC_API_KEY` | `VF_CLAUDE_BASE_URL` |
| Qwen2.5-7B | OpenAI 兼容 `/chat/completions` | `VF_QWEN25_API_KEY` | `VF_QWEN25_BASE_URL` |
| Llama-3.1-8B | 同上 | `VF_LLAMA_API_KEY` | `VF_LLAMA_BASE_URL` |
| Qwen3-30B | 同上 | `VF_QWEN3_API_KEY` | `VF_QWEN3_BASE_URL` |
| Fin-o1-8B | 同上 | `VF_FINO1_API_KEY` | `VF_FINO1_BASE_URL` |

base URL 应包含 `/v1`，不包含末尾 `/chat/completions` 或 `/messages`。开放权重模型可以使用用户已有的 vLLM 服务或第三方托管，代码不要求本机加载四个 LLM。明确不需要 GPT-4o-mini、额外 judge、基线模型或 LoRA 训练。

本地检索使用固定版本 BGE embedding 与 cross-encoder，不需要付费 embedding API。首次使用需要下载这两个公开模型的权重及磁盘空间。

GPT-5.5 使用 `max_completion_tokens=8192`、`reasoning_effort=low`，不发送 temperature；FinanceBench/TAT-DQA 的设置来自论文 §4.2，XBRLFiling 统一采用此设置并记录为工程约定。模型 ID 默认 `gpt-5.5`，不会替换为更新模型。请求参数参考[官方 Chat Completions 文档](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)。

Claude 默认 `claude-haiku-4-5-20251001`。开放权重模型默认分别为 `Qwen/Qwen2.5-7B-Instruct`、`meta-llama/Llama-3.1-8B-Instruct`、`Qwen/Qwen3-30B-A3B`、`TheFinAI/Fino1-8B`。论文没有提供全部不可变快照，尤其不能断言默认 Qwen3 变体和历史 Fin-o1 权重就是作者原实验快照；实际服务身份需要记录。

如果服务对 thinking、chat template、token 参数或授权头有特殊要求，请同时说明。配置支持模型级 `parameters` 和数据集级 `dataset_parameters`，具体设置会进入续跑身份和请求审计。

SEC 下载联系方式已由用户提供。两个正式数据集的资产状态以 `research/readiness.json` 为准。TAT-DQA 的索引和财报缺口不再影响当前运行；注册表差异仍见复现说明。
