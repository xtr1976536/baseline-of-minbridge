# GBFR 复现

## 结果

| 数据集与版本 | 样本 | 固定两位准确率 | 参考显示精度准确率 |
| --- | ---: | ---: | ---: |
| FinQA R25，预冻结评分 | 10 | 50% | 60% |
| 同一预测，运行后单位解析修正诊断 | 10 | 60% | 70% |

| R25拒答指标 | 本次结果 |
| --- | ---: |
| 拒答召回 | 1/2（50%） |
| 误拒 | 0/8 |
| 技术错误 | 0 |

全量实验暂停，最新为R25 FinQA 10题验证。第二行是同一批预测经单位解析修正后的评分；TAT-QA本轮未重跑。底座为 `gpt-5.6-sol`，图谱由公开资产重建。

## 安装与检查

Python 3.11+，在本目录执行：

```bash
python -m pip install -c requirements.lock.txt -e ".[test]"
python scripts/bootstrap.py --offline
python -m gbfr.cli check --config configs/main.json
python -m pytest -q
python scripts/offline_smoke.py
```

首次下载资产时去掉 `--offline`。当前暂停状态可通过 `python scripts/run_full_r19.py --mode status` 查看；API配置见下方说明。

## 资料

- [R25结果与审计](docs/FINQA_FRESH_R25_20261107.md) · [历史运行与日志](runs/)
- [主实验数据](data/main/) · [重建图谱](data/assets/) · [原始资料](materials/)
- [重建说明](docs/RECONSTRUCTION.md) · [API配置](docs/API_REQUIREMENTS.md)

[返回仓库总览](../../README.md)。
