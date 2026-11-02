# 配置

`react-*-author-extracted.py` 是从作者 notebook 抽取的函数与环境定义。模型、API 模式、样本数通过运行脚本参数提供。

API 密钥只读取环境变量，不写入仓库。初期日志包含本机绝对路径，但不包含 API 密钥。

PoT使用隔离环境及脚本内固定的发布协议，配置记录在`reproductions/pot/results/*-full-greedy-20261102/config.json`，不覆盖本目录配置。三个金融任务均已完成；结果与复现命令见[PoT说明](../reproductions/pot/README.md)。GBFR使用其独立配置与暂停限制，见[GBFR说明](../reproductions/gbfr/README.md)。

ReAct HotpotQA：500题，EM49.20%、F1 64.90%。[完整结果与配置](../docs/react/README.md)。

## Self-Refine发布配置

GSM8K 1319题已完成，初始96.2851%、最终96.1334%。最终配置为[config.json](../reproductions/self-refine/results/gsm-full-final-20261102/config.json)；固定温度0.7、最多4轮、初始300/反馈600token，同一gpt-5.6-sol。原全量与补齐源码快照在[archive](../reproductions/self-refine/archive/)，代码哈希与配置吻合。安装、离线核验见[Self-Refine README](../reproductions/self-refine/README.md)。这套配置独立于Logic-LM、ReAct、PoT和GBFR，不覆盖已有设置。
