# 四模型配置

| 模型 | 配置与使用 | 冻结结果 |
| --- | --- | --- |
| Logic-LM | [完整说明](../docs/logic-lm/README.md) | [实验索引](../experiments/final/index.json) |
| ReAct | [完整说明](../docs/react/README.md) | [HotpotQA配置与日志](../experiments/react/hotpotqa/) |
| PoT | [完整说明](../reproductions/pot/README.md) | [三任务发布目录](../reproductions/pot/results/) |
| Self-Refine | [完整说明](../reproductions/self-refine/README.md) | [最终GSM配置](../reproductions/self-refine/results/gsm-full-final-20261102/config.json) |

四模型均采用gpt-5.6-sol，具体参数、作者参考模型和适配范围分别记录。密钥只读取本机.env或环境变量。各模型独立配置，不将不同运行的输出混写。模型成绩见[统一总览](../README.md)。
