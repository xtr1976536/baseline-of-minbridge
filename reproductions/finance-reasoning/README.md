# FinanceReasoning 复现

## 结果

| 数据集 | 样本 | 正确 | 本次准确率 | 论文表5 |
| --- | ---: | ---: | ---: | ---: |
| FinanceReasoning Hard | 238 | 217 | 91.18% | 91.60% |

本次底座为 `gpt-5.6-sol`，论文为 `gpt-4o-2024-11-20`。评分采用0.2%相对误差，零值精确匹配。

## 方法

生成检索查询 → Contriever检索前30个函数 → 同一LLM筛选至多3个 → PoT生成并执行Python。数据包含Hard 238题与3,133条函数。

## 安装与运行

Python 3.11+，在本目录执行。模型权重与索引需首次下载、重建。

```bash
python -m pip install -c requirements.lock.txt -e ".[test]"
python scripts/bootstrap.py
python -m fr_repro check --config configs/portable.gpt56sol-executor-v3.json
python -m pytest -q
# 设置 FR_GPT56SOL_API_KEY 后运行
python -m fr_repro run --config configs/portable.gpt56sol-executor-v3.json
```

## 资料

- [最终逐题结果与日志](runs/aiwanwu-gpt56sol-executor-v3/) · [结果报告](docs/RESULTS_EXECUTOR_V3.md)
- [数据集与函数库](data/) · [论文](paper/2025.acl-long.766.pdf)
- [实现说明](docs/REPRODUCTION.md) · [执行器修改](docs/EXECUTOR_V3.md) · [历史运行](runs/)

[返回仓库总览](../../README.md)。
