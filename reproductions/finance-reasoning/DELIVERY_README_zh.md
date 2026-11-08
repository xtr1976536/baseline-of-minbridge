# FinanceReasoning 最新完整交付包

打包日期：2026-11-08（Asia/Shanghai）。最终实验完成日期：2026-11-06。

## 最新结果与论文对比

- 仅复现论文表5最佳方法：LLM生成检索查询 → Contriever检索前30函数 → 同一LLM筛选至多3个 → PoT生成并执行Python。
- Hard全238题，217题正确，准确率91.18%；程序执行失败0，筛选格式失败0，最终接口错误0。
- 论文表5为91.60%，本次低0.42个百分点，按238题折算约差1题。
- 论文使用gpt-4o-2024-11-20；本次为用户指定的第三方接口gpt-5.6-sol。属于替代骨干的方法复现，不是同模型严格复现。
- 保持238题与0.2%相对误差标准，未用标准答案调整修复规则。105项测试通过。
- 本次未运行同骨干的无增强对照，因此没有验证论文所述+8.41个百分点的知识增强增益。

## 阅读顺序

1. finance_reasoning/docs/RESULTS_EXECUTOR_V3.md：最新完整结果。
2. finance_reasoning/docs/EXECUTOR_V3.md、SELECTOR_IDS_V2.md：两轮最小修复及公平性。
3. finance_reasoning/runs/aiwanwu-gpt56sol-executor-v3/：最终238题逐题预测、程序、指标和运行清单。
4. finance_reasoning/research/executor_v3_gold_free_run_audit.json、executor_v3_preregistered_protocol.json、executor_v3_final_validation.json：冻结协议及审计。
5. finance_reasoning/README.md、docs/REPRODUCTION.md：方法与环境说明。
6. paper/2025.acl-long.766.pdf：原论文（表5在PDF第8页，模型版本表19在第29页）。

## 包含内容

原始源码、提示词、原始及本地配置、测试、依赖锁、全部保留的历史实验/缓存、原始238题、3133函数库、原论文、代码修改补丁、审计、最新105项测试XML与已核验wheel。完整包另含固定版本Contriever权重及实际使用的函数嵌入索引；轻量附件包省略的两个大文件在各自清单中列出。

原实验文件与绝对路径配置保持原样，未改写冻结记录。额外提供可移植配置finance_reasoning/configs/portable.gpt56sol-executor-v3.json，仅调整目录到相对路径并使用新输出/缓存目录；它不是原实验冻结配置，不覆盖既有结果。

## 安装及复查（不调用模型API）

在Python 3.11+环境，进入finance_reasoning目录：

    python -m pip install -c requirements.lock.txt -e ".[test]"
    python -m fr_repro check --config configs/portable.gpt56sol-executor-v3.json

完整包已含检索资产。轻量包先执行python scripts/bootstrap.py下载固定版本权重并重建索引，再check。Windows/Python3.12为原验证环境，包内不含Python虚拟环境及可由依赖锁安装的库。

如需另启实验，先自行在当前终端设置FR_GPT56SOL_API_KEY环境变量，然后使用上述portable配置运行python -m fr_repro run --config configs/portable.gpt56sol-executor-v3.json。该命令会产生新的付费API请求；阅读已有结果无需API。原scripts/run_aiwanwu.ps1依赖原电脑的DPAPI凭据，其他电脑请使用环境变量方式。

## 安全与完整性

包内不含API密钥、DPAPI凭据、.env私密文件或账户登录信息。已排除临时浏览器脚本、Python字节码、构建副本、测试缓存和HuggingFace下载缓存；保留正式测试报告和已验证wheel。提供每个有效载荷文件的SHA256清单及压缩包SHA256。未启动任何新实验。
