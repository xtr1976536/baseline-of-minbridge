# R21 ETR 单题只读复核

样本：`FinQA:ETR/2017/page_143.pdf-3`。本审查0次API调用，只新增本JSON/Markdown审计文件，未修改代码、数据金标、运行结果或快照。

## 结论

此题没有显示图谱公式缺口，也不能证明新增图谱公式生效。轨迹为`OQA → OES → OES → OPE.final`，没有OMD或OPE.metric。

当前输出是`56680.8`，元数据为`currency=USD, scale=thousand`。`760000 × 7.458 / 100 = 56680.8 thousand USD = 56,680,800 USD`，因此百分比及输出单位处理正确。不能仅比较裸数值而诊断成缺少单位换算。

原始FinQA自身的程序/执行结果与发布答案相差10倍。数值与原始程序一致仅说明算术一致，尚不能证明利率适用范围成立；本审查不修改或重算冻结评分。

## 精确源证据

源文件：`data/raw/official/FinQA.json`，原始ID：`ETR/2017/page_143.pdf-3`。

- `qa.answer`：`566808000`
- `qa.program`：`multiply(760000, const_1000), multiply(#0, 7.458%)`
- `qa.exe_ans`：`56680800.0`
- `qa.steps[0]`：`{"op": "multiply1-1", "arg1": "760000", "arg2": "const_1000", "res": "760000000"}`
- `qa.steps[1]`：`{"op": "multiply1-2", "arg1": "#0", "arg2": "7.458%", "res": "566808000"}`

最后一步`res`与`qa.answer`均为566,808,000，但程序中的`7.458%`应用于760,000,000所得为56,680,800，与`qa.exe_ans`一致。没有依据为拟合发布答案再乘10。

## 当前D和轨迹证据

当前样本：`data/validation/gbfr_live_r21/repair/FinQA.jsonl`；当前预测：`runs/gbfr_e2e_validation/r21/repair/GPT-5.6 Sol/FinQA/predictions.jsonl`。完整D、OQA、OES、最终程序保存在配套JSON。

利率的原文限定：

> ( d ) this note did not have a stated interest rate , but had an implicit interest rate of 7.458% ( 7.458 % ) .

本金的原文限定：

> the annual long-term debt maturities ( excluding lease obligations and long-term doe obligations ) for debt outstanding as of december a031 , 2017 , for the next five years are as follows : amount ( in thousands ) .

对应表格为：

```text
|  | Amount (In Thousands) |
| --- | --- |
| 2018 | $760,000 |
```

OQA将金额约束为`entity_scope="Entergy long-term debt", temporal_scope="2018"`，但利率的`entity_scope`和`temporal_scope`均为null。OES提取7.458时只保留`implicit interest rate`标签，未证明其适用于上述aggregate maturities。

当前输出程序：

```python
def compute(vars):
    amount = vars["v1"]
    rate = vars["v2"]
    interest = amount * rate / 100
    return {
        "value": interest,
        "trace": {
            "amount": amount,
            "rate_percent": rate,
            "interest": interest,
            "output_meta": {
                "currency": "USD",
                "scale": "thousand",
                "unit": None
            }
        }
    }
```

当前金标`answer_meta={}`，未显式声明裸数字答案的单位。本审查保留该事实，不替评分器推定金标单位。

## 剩余scope风险与通用建议

7.458%属于原文的“this note”，本金则是排除租赁和DOE负债后的全体年度债务到期金额。所给D未明确证明二者是同一债项或覆盖范围。维度相容、文本中存在唯一利率，均不足以证明金融适用关系；这属于尚未建立的关联，不是证明该利率绝不适用。

建议OQA保留百分比与数量的主体、工具/债项、期间、覆盖范围及计价口径，并在OES或最终关系检查要求Q/D中的明确绑定或直接蕴含。关联不明应拒答。命名财务指标仍按论文OMD流程处理，不应借简单乘法添加未给出的金融公式，不按gold追加系数。
