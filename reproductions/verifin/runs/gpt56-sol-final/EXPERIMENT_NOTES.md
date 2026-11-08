# 本次主实验说明

本次按用户要求使用 AIwanwu 的 `gpt-5.6-sol`，完整运行 FinanceBench 公开数值子集 67 条。所有 LLM 阶段使用同一骨干、low reasoning、8192 completion tokens，不发送 temperature。检索模型与参数在正式预测前固定，具体 revision 见 `configs/main.json`。不运行基线、repair、消融或训练；XBRLFiling 600 条已准备但未运行。

67 条原样保留。TA=18、FA=6、TR=1、FR=1、弃答=39、正确性未决=2、运行错误=0、遗漏=0。指标与 95% 精确置信区间见 [主结果](main_results.md)。2 个未决判定的参考答案含多个数值目标，因此不任取其中一个作为唯一金标，仍保留在覆盖率分母中。

本次没有复现论文的零误接受结论。6 次 FA 按冻结的原始参考标签严格计分；其中 5 次是金额小数与参考 `.00` 金额之间小于 0.5 百万美元的差异（1615.9/1616.00、381.603/382.00、3215.4/3215.00、302.578/303.00、5466.312/5466.00），另外 1 次为 Pepsi 重组费用 0 与参考 411 百万美元不符。没有改金标、放宽容差、删去误接受或为获得更好答案而重采样。详见 `research/main_error_cases.json`。

39 项离线测试通过；28 份接受/拒绝 SMT 证明已独立重放，SAT/UNSAT 均与保存判定一致。证明重放核对的是保存约束的求解结果，答案正确性单独按原始标签评测。两份 earnings 文档没有发布 XBRL instance，继续保留在 67 条分母中。

完整原推理输出保留在 `runs/gpt56-sol-v3/`。结束后对参考答案显式单位优先级做了确定性修正，并统一重算 67 条；正确性与所有指标均未改变，原始候选、验证判定、检索和证明保持不变，没有新推理调用。版本和迁移审计见 `research/implementation_versions/final_scoring_audit.json`。首批单位归一化修正与并发处理变更也保留独立版本，候选答案一直复用相同请求缓存。

本次骨干由用户指定，公开注册表也与论文 v3 报告的资产数量不同；只能视为带明确差异记录的方法复现，不能声称等同于原论文六骨干的精确数值复现。平台返回的模型标识为 `gpt-5.6-sol`，没有独立验证第三方服务的底层权重。

逐题记录：`GPT-5.6-Sol/FinanceBench/predictions.jsonl`；指标：同目录 `metrics.json`；证明：同目录 `smt/`。当前 `configs/main.json` 仅包含本次完成的 FinanceBench。密钥通过 Windows DPAPI 加密保存在项目外，使用 `python scripts/run_main.py run` 在进程内加载；不需要补充其他 API。
