# 配置

`react-*-author-extracted.py` 是从作者 notebook 抽取的函数与环境定义。模型、API 模式、样本数通过运行脚本参数提供。

API 密钥只读取环境变量，不写入仓库。初期日志包含本机绝对路径，但不包含 API 密钥。

PoT使用隔离环境及脚本内固定的发布协议，配置记录在`reproductions/pot/results/*-full-greedy-20261102/config.json`，不覆盖本目录配置。三个金融任务均已完成；结果与复现命令见[PoT说明](../reproductions/pot/README.md)。GBFR使用其独立配置与暂停限制，见[GBFR说明](../reproductions/gbfr/README.md)。

ReAct HotpotQA：500题，EM49.20%、F1 64.90%。[完整结果与配置](../docs/react/README.md)。
