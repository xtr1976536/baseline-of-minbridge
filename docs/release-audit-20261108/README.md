# 2026-11-08 三模型入库审计

新增 FinanceReasoning、GBFR、VeriFin，按 reproductions/<model>/ 保存代码、配置、依赖锁、测试、数据、历史及最终运行日志、逐题输出与审计。原四模型冻结结果未修改。原作者/历史文档保留原文，项目导航README更新至七模型。

## 来源与选择

GBFR完整包与VeriFin合并包SHA256均与交付邮件匹配；所有ZIP通过CRC检查。FinanceReasoning轻量包SHA256为 a7e26b507f2489ba29a8375f7391f35ee904b42fc57b173286776cfc83dffa77，未提供外部预期哈希。轻量包缺少Contriever权重和索引，按原bootstrap下载重建。

不上传虚拟环境、临时构建wheel。正式测试XML迁移至 research/test-reports。VeriFin原始174MB ZIP替换为三个字节分卷，见 data/raw/tatdqa/ARCHIVE_PARTS.md；excluded.json记录原路径未直接收录，不代表数据丢弃。SOURCE_PACKAGE_MANIFEST为原包清单，当前文件以本目录manifest.json为准。

## 预检查

45189个新增模型文件逐一计算SHA256，1048个Python文件语法解析通过；未发现超过100MB单文件或常见令牌/私钥模式。该扫描不构成对所有敏感信息的绝对保证。未调用付费API，未重跑模型，未改逐题预测。当前Python未安装pytest，因此未重新执行交付包中的模型测试；交付原测试报告保留。

## 上传后检查

两轮远端核查结果另记 post-upload-checks.json：第一轮读取远端Git树核对路径、大小和blob；第二轮从远端重新获取提交并验证对象完整性及发布manifest。历史原文中的机器绝对路径仅作证据，运行优先使用portable配置与各模型安装说明。

两轮上传后检查均通过：GitHub API核对 FinanceReasoning 3184、GBFR 33325、VeriFin 8680 个文件的完整blob映射；重新fetch后git fsck无异常，45189个文件SHA256复查一致。仅检查资料发布完整性，未重跑付费实验或宣称新的测试通过。
