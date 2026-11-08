# VeriFin 最新完整交付包（2026-11-08，Asia/Shanghai）

本包仅对应本聊天的 VeriFin 主模型复现项目，不包含父目录 GBFR、FINDER 或其他项目。

## 先看这些文件

1. verifin/README.md：安装、配置、历史实验及最新状态。
2. verifin/runs/financebench-full-post35-v1/comparison.md：最新完整 67 题与修改前、论文的对比。
3. 同目录 response_review.json、validation.json、scoring_disagreements.json：语义问题、完整性及两种评分差异。
4. verifin/docs/API_REQUIREMENTS.md：API 配置说明，密钥需由接收方另行提供。

最新结果：FinanceBench 67 题，GPT-5.6 Sol；复用原 35 条记录，补跑 32 题。
主舍入口径为本地预先声明的操作化规则，不是作者公布的官方阈值：接受精度 100%，决策准确率 100%，覆盖率 67.16%。
1 条正确性未决不计入常规准确率；把它保守计作错误，决策准确率为 97.78%。
旧严格显示精度口径：80% / 81.82% / 67.16%。覆盖率低于论文 70.1%，不能声称全部达标。
运行错误与遗漏均为 0；另有 1 条非 JSON 输出被当前解析器记为弃答，税率题也存在重复百分比换算的问题，详见复核报告。

## 内容与边界

包含当前源代码、配置、测试、脚本、论文原 PDF 与摘录、复现说明、全部已保存历史结果、SMT、请求/响应审计缓存、数据集、原始财报与规范化事实。
已准备但未运行的其他数据资产也原样保留，不代表本次执行了这些实验。
upstream/results 是作者仓库附带的历史资产，不是本地复现结果；本地结果在 verifin/runs。
不含 API 密钥、DPAPI 凭据、实际 .env、Git 历史、Python 环境、编译缓存、临时文件或可重建的嵌入缓存；示例 .env.example 保留。
检索模型权重和 Python 依赖需按 README 安装/下载，未从用户电脑的全局缓存复制。
源文件未因打包而改写；包内文件通过清单 SHA-256 与 ZIP CRC 检验。

## 使用

先完整解压，再进入 verifin 目录；相对路径、数据和历史报告的目录结构保持不变。
只查看结果无需 API。安装依赖后可用 python scripts/report_full_post35.py 离线重放完整性和算术审计。
若需重新推理，请先阅读 README，并配置自己的接口凭据；不要覆盖已冻结的实验目录。
PACKAGE_MANIFEST.json 和 SHA256SUMS.txt 列出交付的逐文件大小与哈希。
