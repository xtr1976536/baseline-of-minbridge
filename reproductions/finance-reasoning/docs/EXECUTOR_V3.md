# 剩余五题程序失败的修复与全量重跑

**已完成：217/238，准确率 91.18%；程序失败、筛选失败和未解决接口错误均为 0。** [完整结果](RESULTS_EXECUTOR_V3.md)。

用户要求：检查上一轮五题程序或执行失败的原因，按照论文思路做尽可能小、严格公平的修复，不用标准答案调整，然后完整重跑 238 题。

## 不读取标准答案数值的诊断

仅检查旧的生成程序、报错以及原问题的输出单位要求：

| 原问题 ID | 原失败原因 | 统一修复 |
|---|---|---|
| test-2011 | 程序返回一个带 `%` 的数值字符串，题目明确要求百分数 | 按题目预先声明的百分数输出契约解析完整单值 |
| test-2071 | 同上 | 同上 |
| test-2136 | 同上 | 同上 |
| test-2167 | 同上 | 同上 |
| test-2020 | `statistics.NormalDist` 被数学执行器的导入白名单误拦截 | 补充允许这一标准数学类 |

没有查看标准答案数值、标准解或旧答案的正误来决定修复方式。旧五段程序原文重放后均能执行；检查只确认可执行性，不据此判断答案正确性。详情在 `research/executor_v3_failure_diagnosis.json`。

## 修改边界

1. `statistics` 原本已允许，`cdf` 等方法也已允许；仅补入 `NormalDist` 名称，不开放任意导入，不添加金融公式或额外软件依赖。[Python 标准库说明](https://docs.python.org/3.12/library/statistics.html#statistics.NormalDist)。
2. 原问题明确要求答案/结果为百分数时，允许生成程序返回完整的有限单值百分数字符串。例如合成值 `7.25%` 解析为所要求百分数表示中的数值 `7.25`，同时保存原字符串和表示类型。没有乘除 100，也没有尝试多种尺度来匹配金标。
3. 输出契约在模型调用前只根据原问题的明确单位指令确定；要求小数/分数、仅背景提及百分数或指令不明确时，不猜测百分号应如何处理。原生数字或布尔结果始终不因单位标记而变换。
4. `7% or 8%`、混合金额单位、算式、非有限值等仍拒绝；不从多值中挑一个、不执行字符串算式。百分数点差不会自动当成百分率。

作者原评测程序同样对百分号作表示归一化。本实现保留这一有限格式支持，并增加题目单位约束；不采用原程序中的任意 `eval`、广泛删除单位或任取列表首值的行为。

变化只涉及 `execution.py`、`worker.py` 和执行器调用处的 `runner.py`。查询、函数筛选、PoT 提示词、编号协议、模型参数、数据、检索器和 0.2% 相对误差评分均不变。没有改写生成程序的计算步骤。

## 冻结与重新运行

105 项测试通过，涵盖正态分布、明确/冲突的单位指令、数值和符号保留、无尺度变换及不合法返回值拒绝。源码、配置和哈希在新实验请求前写入 `research/executor_v3_preregistered_protocol.json`。

```powershell
.\scripts\run_aiwanwu.ps1 -Config configs/local.aiwanwu-gpt56sol-executor-v3.json
```

对全部 238 题从空缓存重新生成查询、筛选及程序，不仅重做旧五题，不复用旧正确回答。新输出：`runs/aiwanwu-gpt56sol-executor-v3/`；新缓存：`runs/aiwanwu-gpt56sol-executor-v3-cache/`。旧运行保留。

正式准确率在全部新预测保存后统一计算，中途不按准确率改变规则。没有程序纠错模型调用、答案条件重试或默认回退。仍使用用户指定的 `gpt-5.6-sol` 替代骨干。

## 本轮接口中断与完成

成功完成 77 题后，接口两次 HTTP 403 使运行停止；当时余额查询约 0.04 美元。原参数的失败阶段重试成功响应保存在同一运行缓存。用户补充余额后，按完全相同的源码和参数恢复，现已完成全部 238 题。

控制器在中断时自动生成了标记为 partial 的汇总，它只作为中断记录保留，没有用于修改源码、提示词或参数。恢复时只处理接口失败和未完成题，复用本轮已成功响应；没有从其他实验取答案或按正确性挑选输出。

恢复命令为：

```powershell
.\scripts\run_aiwanwu.ps1 -Config configs/local.aiwanwu-gpt56sol-executor-v3.json -RetryErrors
```

最终核验见 `research/executor_v3_gold_free_run_audit.json` 和 `research/executor_v3_final_validation.json`；进度和中断历史保留在 `research/executor_v3_checkpoint.json`，代码差异为 `research/executor_v3_code_changes.patch`。
