# 本次需要的 API

2026-11-06 接入更新：用户已明确指定 `gpt5.6sol`。已通过模型列表确认实际 ID 为 `gpt-5.6-sol`，地址 `https://aiwanwu.cc/v1`；非流式 Chat Completions 调用成功，前两题的全部六次阶段调用均返回该模型。单独使用 `configs/local.aiwanwu-gpt56sol.json` / `runs/aiwanwu-gpt56sol-final/`，报告记录骨干替换。密钥在项目外以 Windows DPAPI 加密保存，`scripts/run_aiwanwu.ps1` 解密后只放入当前子进程的 `FR_GPT56SOL_API_KEY`。以下为论文原 GPT-4o 要求，供保留对照。

只需要 **GPT-4o 文本推理 API** 一种；查询、函数筛选和 PoT 三阶段共用。论文表 19 指定快照 **`gpt-4o-2024-11-20`**，优先保持该版本，不自动换成 GPT-5 或其他新模型。

请提供：

| 内容 | 要求 |
|---|---|
| Base URL | OpenAI Chat Completions 兼容地址，通常以 `/v1` 结尾；程序追加 `/chat/completions` |
| Model ID | 平台实际接受的、对应 `gpt-4o-2024-11-20` 的 ID，最好能确认真实后端快照 |
| API Key | 放入本机环境变量 `FR_GPT4O_API_KEY`，不写入代码或结果文件 |
| 限额 | 如有 RPM、TPM、并发、上下文长度或输出 token 上限，请一并说明 |

程序发送非流式消息 `model/messages/stream=false/n=1`，包括 system 和 user 两个角色；参数固定为 `temperature=1.0`、`top_p=1.0`、`max_tokens=8192`。需要兼容 `choices[0].message.content`、`finish_reason=stop`；记录 `usage`、服务返回的模型名和指纹。函数候选较长，接口应支持 GPT-4o 的长上下文，不能静默截断候选或原文。

如果平台返回别名、不同快照或隐藏映射，必须记录实际服务说明，不能仅凭展示名宣称快照相同。论文使用官方 API；第三方兼容服务可接入，但服务差异会如实记录。

完整主实验为 238 道题，每题 3 次成功调用，约 **714 次文本调用**，另加接口失败重试；先用前两题验证，成功后保留它们并续跑余下问题。

**不需要 DeepSeek-R1、Claude、GPT-4o-mini、GPT-5、Qwen 或 embedding API。** Contriever 及 3,133 条函数在本地运行，PoT 结果由 Python 执行，不调用答案提取模型。

```powershell
$env:FR_GPT4O_API_KEY = "你的密钥"
$env:FR_GPT4O_BASE_URL = "https://你的服务地址/v1"
python -m fr_repro run --limit 2
python -m fr_repro run
```

模型 ID 在 `configs/main.json` 的 `llm.model` 中设置；地址支持上述环境变量覆盖。`.env.example` 不自动加载。当前没有真实推理 API 调用。

依据：[官方 GPT-4o 文档](https://developers.openai.com/api/docs/models/gpt-4o)、[官方请求格式](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)。
