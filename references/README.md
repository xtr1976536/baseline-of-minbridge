# 参考文献

- ReAct: Synergizing Reasoning and Acting in Language Models，ICLR 2023。https://arxiv.org/abs/2210.03629
- Logic-LM: Empowering Large Language Models with Symbolic Solvers for Faithful Logical Reasoning，Findings of EMNLP 2023。https://aclanthology.org/2023.findings-emnlp.248/

本目录原文用于结果核验与研究参考，论文版权归各自权利人。benchmark 与作者输出通过 upstream 固定版本获取，不改变原始许可。

- PoT: Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks，TMLR 2023。[论文](https://arxiv.org/abs/2211.12588v4)，[作者代码](https://github.com/TIGER-AI-Lab/Program-of-Thoughts)。金融三数据集全量已完成，见[复现与结果](../reproductions/pot/README.md)。
- GBFR保留为独立复现任务，当前暂停正式全量，见[状态与差异](../reproductions/gbfr/README.md)。

更新后的论文清单PDF及其源文件位于[docs/references](../docs/references/)。总项目进展以[根README](../README.md)为入口；第三方作者README保留原文。

ReAct HotpotQA 500题复现结果：EM49.20%、F1 64.90%，见[结果表](../docs/react/README.md)。

## Self-Refine

Self-Refine: Iterative Refinement with Self-Feedback，NeurIPS2023。[正式论文](https://proceedings.neurips.cc/paper_files/paper/2023/file/91edff07232fb1b55a505a9e9f6c0ff3-Paper-Conference.pdf)；[作者代码](https://github.com/madaan/self-refine)。本项目已完成GSM8K 1319题替代底座主实验，初始96.2851%、最终96.1334%，累计曾正确97.9530%单独报告；不将累计指标当最终准确率。其余六任务未完成。见[方法与结果](../reproductions/self-refine/README.md)及[两轮检查](../reproductions/self-refine/docs/release-checks/)。
