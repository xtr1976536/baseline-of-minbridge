# 四模型三轮整理检查

## 第一轮：清单与保护

四模型代码、实验和日志逐文件哈希保护；结果见round1.json。GBFR专属目录与过时混合候选清单移到仓库外归档，当前Git版本移除，不重写历史。四模型真实证据不删；Self-Refine烟雾测试samples仅删除与同目录predictions.jsonl逐对象完全一致的重复文件。

## 第二轮：离线验证与文档

结果见round2.json及四份validation.txt。运行Logic-LM发布完整性、ReAct发布验证、PoT FinQA完整性与Self-Refine发布验证，不调用模型API。PoT另外两个冻结任务的官方评分记录与完整ID/gold再次核查。所有项目README本地链接核验；四模型统一范围、结果、适配、运行、证据、验证六项结构。

## 第三轮：Git发布内容独立检查

结果见round3.json。从暂存区文件读取并独立解压关键证据、核对样本分母和分数、扫描密钥、核验排除目录不再被跟踪。保护清单的所有非README代码/证据保持不变，只有已验证完全重复的smoke子文件移除。第三方作者README不改。

本次不重新生成答案、不重新执行全部生成程序、不改变任何冻结指标。完成范围仍为Logic-LM五集、ReAct HotpotQA500、PoT金融三集、Self-Refine GSM8K1319。不是四篇论文所有任务都完成。

## 2026-11-08 仓库扩展

仓库现收录七个模型，新增 FinanceReasoning、GBFR、VeriFin。此目录原有结果与范围保持原记录；最新模型范围、结果限制及导航见[仓库总览](../../README.md)。
