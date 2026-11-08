# 源级参数绑定修复与独立保守图候选

修复的是Python局部形参与全局金融指标同名导致的绑定错误。只在同一源记录明确声明的related_concepts范围内，使用其原始注册别名或参数docstring的明确指标标签做唯一映射；不按参数位置、算式形状或金融常识补身份，不修改全局别名映射。

## 建议用于下一步小样本的候选

`data/assets/fmkg.reconstructed_candidate_v2_conservative.json`
SHA-256：`bc6bdbe2d88a2effc9c4709b3207687c2d8e580557ec733fe5754b2ac76402bc`。

- 保留全部11,619个节点与其名称、别名、定义和来源记录。
- 保留原4,844条公式的完整对象，不仅保留ID；移除0条。
- 新增108条有唯一局部参数证据且源数学式/代码符号等价的公式；40个旧原子节点获得源公式。
- 新结构：atomic 8,309、derived 3,310、edges 12,104，最大深度6。
- 173条满足新证据条件且不在旧图的源公式中，13条成环、47条令旧祖先超深、5条涉及旧图未有节点，均整式跳过。
- 新增顺序只按原始源记录、公式下标、稳定公式ID决定，不读取问题、预测或金标来选择方向。
- 等价方程/百分比显示变体不会作为额外独立投票路径。

参数证据计数：{'record_local_explicit_alias': 113, 'explicit_parameter_documentation': 3}。

完整源重建另存 fmkg.reconstructed_candidate_v2.json：新增231、移除146条旧公式，其中117条仍可解析但受重排/去重/成环裁剪影响，29条在局部代码角色下出现新身份分歧。该全量重建仅供审计，不作为当前推荐候选，也不把这些删除静默带入保守图。

## 必须保留的限制

record5（Debt-to-Asset Ratio）没有被强行恢复：assets有明确注册别名可局部绑定Total Assets，liabilities没有Total Liabilities的对应别名或形参文档，仍不能证明其身份。不会选择另一个有公式的Debt Ratio节点来代替。

原图与main_assets.lock.json均未修改。新图继承policy、source_sha256、benchmark_inputs_used=false和reconstructed=true，并增加候选修复说明。候选不是作者未公开专家图谱，不声称所有图缺口已解决。

24项图谱相关测试通过，包含局部/全局名冲突、显式文档绑定、限定词不被抹除、局部歧义、多参数角色碰撞、真实算术分歧，以及旧DAG完整保留、成环跳过、超深跳过和等价百分比不重复投票。

逐公式新增/跳过和完整参数证据：graph_candidate_v2_conservative/graph_extension.json；全体源公式决策：同目录source_formula_decisions.json。
