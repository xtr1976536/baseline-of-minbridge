GBFR 最新完整资料包（2026-11-08，Asia/Shanghai）

入口：README.md 和 docs/FINQA_FRESH_R25_20261107.md。
本包包含当前代码、依赖锁、测试、完整冻结数据/图谱、论文与上游来源、全部GBFR实验/缓存/失败记录、版本快照和最新审计。
R25仅运行全新FinQA10题，TAT-QA未重跑；全量仍暂停，旧R19为1401条记录。
原先冻结评分为固定两位50%／参考显示精度60%；单位解析修正对同一预测的运行后诊断为60%／70%，原记录均保留。
拒答召回50%(1/2)，误拒0/8，技术错误0；430项测试通过，不能宣称已全面达到论文指标。

安装：Python3.11+；python -m pip install -c requirements.lock.txt -e ".[test]"
离线检查：python -m pytest -q
API凭据必须由接收者自行在环境变量中设置，本包不包含真实API密钥；不要从旧运行断点自动恢复全量。

PACKAGE_MANIFEST.json 记录打包文件的原始与交付SHA-256、大小、必要脱敏与排除项。历史配置保留原机器路径，作为审计快照；当前入口的路径由解压后工作区解析。
未包含可重新生成的.git、虚拟环境、字节码、构建/临时目录；同目录独立FINDER/VeriFin/finance_reasoning项目不属于本次GBFR交付。
