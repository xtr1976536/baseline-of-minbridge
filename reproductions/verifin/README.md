# VeriFin 复现

## 结果

| 数据集 | 样本 | 评分口径 | 接受精度 | 决策准确率 | 覆盖率 |
| --- | ---: | --- | ---: | ---: | ---: |
| FinanceBench | 67 | 本地主舍入 | 100% | 100% | 67.16% |
| FinanceBench | 67 | 旧严格显示精度 | 80% | 81.82% | 67.16% |
| 论文参考 | — | 论文GPT-5.5 | 100% | 86.7% | 70.1% |

底座为 `gpt-5.6-sol`。主舍入是本地评分规则；1条正确性未决不计入常规准确率分母，按错误计入时决策准确率为97.78%。覆盖率低于论文70.1%。

## 安装与运行

Python 3.11+，在本目录执行：

```bash
python -m pip install -c requirements.lock.txt -e ./upstream
python -m pip install -c requirements.lock.txt -e .
python -m pip install -c requirements.lock.txt pytest
python -m vf_repro.runner check
python -m pytest -q
python scripts/offline_smoke.py
# 按API说明设置环境变量后运行；已有记录自动续跑
python scripts/run_main.py run --config configs/financebench-full-post35.json --datasets FinanceBench
```

## 资料

- [67题结果与日志](runs/financebench-full-post35-v1/) · [结果对比](runs/financebench-full-post35-v1/comparison.md)
- [语义与格式复核](runs/financebench-full-post35-v1/response_review.json) · [完整性审计](runs/financebench-full-post35-v1/validation.json)
- [数据与财报](data/) · [历史运行](runs/)
- [复现说明](docs/REPRODUCTION.md) · [API配置](docs/API_REQUIREMENTS.md) · [作者源码](upstream/)

[返回仓库总览](../../README.md)。
