# DCRC 公开材料核查（2026-10-30）

论文：Fighting Numerical Hallucinations via Data-centric Compilation for Online Financial QA，arXiv:2605.31064v1，KDD 2026 ADS。

结论：截至本次核查，未定位到可验证为作者发布的完整代码仓库、DSA训练后权重或专用合成训练集。不能断言作者从未公开或不存在未索引材料。准确描述为“论文给出了方法、附录提示词、表示格式和执行示例，但尚未找到可直接运行的官方实现”，不应称为“已有官方代码只需改API”。

核查范围：
- arXiv摘要页 https://arxiv.org/abs/2605.31064 ：正文入口、提交历史和链接；仅v1；没有给出作者官方仓库/权重链接。
- HTML全文 https://arxiv.org/html/2605.31064v1 ：正文、Implementation Details、附录A/B/C。
- 完整PDF文本搜索github/huggingface/code available/open source/release：未发现发布声明或具体仓库链接。
- GitHub repository search：精确论文标题、2605.31064、DCRC financial；未返回相应官方仓库。
- Web定向搜索：完整标题+github、Data-centric Reasoning Compiler、作者姓名+标题、site:github.com、site:huggingface.co；未定位相应官方发布。
- Hugging Face models API搜索DCRC：空；datasets API只有两条其他命名结果，没有证据与论文相关。
- ACM DOI https://doi.org/10.1145/3770855.3818407 ：浏览工具无法访问，故不能声称已核实ACM附件页面。
- 搜索未定位唯一可确认的作者项目主页；不把同名作者主页当作证据。

公开程度：
| 材料 | 核查结果 |
| --- | --- |
| 任务和框架 | 正文已描述 |
| DSA提示词、JSON schema和错误原因码 | 附录A公开 |
| 证据审计算例 | 附录B公开 |
| 算子注册表示例、#N引用、执行算例 | 附录C公开，属于局部示例 |
| SFT+GRPO主要参数、奖励公式 | 正文已描述，但不构成完整训练实现 |
| 数据合成完整脚本与各阶段prompt | 未找到完整发布 |
| 结构加权SFT与GRPO训练脚本 | 未找到 |
| 端到端推理和正式评测脚本 | 未找到 |
| DSA 1.5B/3B/7B checkpoint | 未找到 |
| 论文专用合成训练数据 | 未找到 |

本仓库dcrc_executor.py为根据论文重建的局部实现，不是从作者仓库获取的代码。Qwen2.5基础模型开源，不能替代专门训练后的DSA。后续Kaggle阶段属于基于论文重建与训练；未公开细节须显式记录实现选择，不可声称逐行官方代码复现。
