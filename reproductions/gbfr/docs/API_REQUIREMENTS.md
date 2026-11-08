# 接入主实验所需 API

2026-11-06 用户指定改用 GPT-5.6 Sol，并提供 AI 万物服务密钥。已确认 `https://aiwanwu.cc/v1/models` 列出 `gpt-5.6-sol`，基础 `/chat/completions` 调用成功。接入配置在 `configs/gpt56_sol.json`，密钥环境变量为 `GBFR_GPT56_SOL_API_KEY`；未将密钥保存到项目文件或请求缓存。该配置按实际模型名称记录，与论文原始 GPT-5 配置分开。具体真实算子验证结果见 `research/reconstruction/gpt56_sol_api_smoke.json`。

以下列出论文原始两种骨干的要求，供后续恢复原骨干或接入 Qwen 时使用。

只需要两种骨干的文本推理 API：GPT-5 和 Qwen3-14B。每种提供以下三项；同一个平台支持两种模型时可以共用地址和密钥。

| 项目 | 内容 |
|---|---|
| Base URL | OpenAI 格式兼容地址，通常以 `/v1` 结尾；程序会追加 `/chat/completions` |
| 模型 ID | 该服务实际接受的 GPT-5 / Qwen3-14B ID；不能只提供平台展示名 |
| API Key | 填入本机环境变量 `GBFR_GPT5_API_KEY`、`GBFR_QWEN_API_KEY`，不写进代码或 Git |

如服务有并发、QPS/TPM、单次输入/输出长度限制，或强制要求某个 thinking/reasoning 参数，也请一并提供服务文档或具体设置。这些是服务配置，论文未披露其精确值，运行时会记录，不据评测成绩调参。

程序发送非流式 Chat Completions 请求：`model`、`messages`、`stream=false`、`n=1`，并读取 `choices[0].message.content` 和 `usage`。四个算子及路径审核全部调用当次实验的同一个骨干；没有另用更强的 judge，也不需要额外的 embedding 服务。

环境变量示例见仓库根目录 `.env.example`；它是说明文件，不会自动加载。实际模型 ID 和可选服务参数填在 `configs/main.json`，接口地址也可用 `GBFR_GPT5_BASE_URL` / `GBFR_QWEN_BASE_URL` 覆盖。收到信息后先做小量真实接口和协议检查，再运行全部八个单元。

官方 GPT-5 文档列有 `gpt-5` / `gpt-5-2025-08-07` 及 Chat Completions 支持；实际账户或代理是否开放这些 ID 仍需由提供的服务确认。保留论文要求的 GPT-5，不自行升级模型。论文没有说明其实际服务商、模型快照或 reasoning 配置。

参考：[GPT-5 模型文档](https://developers.openai.com/api/docs/models/gpt-5)、[Chat Completions 请求格式](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)。

最新接入结果：基础调用、全图 ROE 多跳计算（21.28%）和缺失年份拒答均已通过；124 项离线测试通过。密钥只在当前调用进程内使用。全量实验尚未执行，接入验证不属于正式准确率结果。
