# 赛题一参考论文与阅读笔记

以下 PDF 已下载到本目录。`Martin_2021_ML_Delay_Prediction_author_copy.pdf` 是作者 2023 年博士论文附录 A.1 收录的该论文全文，非 IEEE 排版版本。

## 已通读的论文

| 论文 | 本地文件 | 原文来源 | 与赛题的关系 |
|---|---|---|---|
| Martin, Grewal, Areibi, *A Machine Learning Approach to Predict Timing Delays During FPGA Placement* (2021) | `Martin_2021_ML_Delay_Prediction_author_copy.pdf` | [作者博士论文](https://atrium.lib.uoguelph.ca/bitstreams/b3a0ba73-f762-4ee4-a985-e3e1f9d0a8ed/download)，附录 A.1 | 布线前延时预测；可借鉴特征工程，但目标不是已知加权图上的最短路。 |
| Marquardt, Betz, Rose, *Timing-Driven Placement for FPGAs* (2000) | `Marquardt_2000_Timing_Driven_Placement.pdf` | [作者公开稿](https://www.eecg.toronto.edu/~jayar/pubs/marq/fpga2000_arm.pdf) | 按横纵位移预计算延时矩阵，可借鉴表驱动的查询方式。 |
| Jiang et al., *Critical Path Aware Timing-Driven Global Placement for Large-Scale Heterogeneous FPGAs* (2025) | `Jiang_2025_TD_Placer.pdf` | [arXiv](https://arxiv.org/pdf/2512.00038) | 25 项时序特征与拓扑建模；神经网络推理不能直接视为满足赛题的单线程吞吐要求。 |
| Maidee, Ababei, Bazargan, *Timing-Driven Partitioning-Based Placement for Island Style FPGAs* (2005) | `Maidee_2005_Timing_Driven_Partitioning.pdf` | [作者公开稿](https://people.ece.umn.edu/~kia/Papers/2005/TCAD05_v24_n3_p395_ppff.pdf) | 从已布线样本建立按距离与关键度索引的延时查找表。 |
| Maidee, Ababei, Bazargan, *Fast Timing-Driven Partition-Based Placement for Island Style FPGAs* (2003) | `Maidee_2003_Fast_Timing_Driven_Placement.pdf` | [公开稿](https://www.cs.york.ac.uk/rts/docs/SIGDA-Compendium-1994-2004/papers/2003/dac03/pdffiles/35_1.pdf) | 2005 年论文的早期版本，解释分层切分与延时表构建。 |
| Goldberg, Harrelson, *Computing the Shortest Path: A* Search Meets Graph Theory* (2005) | `Goldberg_2005_ALT_Shortest_Path.pdf` | [Microsoft Research 公开稿](https://www.microsoft.com/en-us/research/wp-content/uploads/2005/01/soda05.pdf) | 与赛题的带权有向图两点最短路查询直接相关；地标与三角不等式给出可证明的下界。 |

另保留 `Martin_2023_PhD_Thesis.pdf`，其第 41–45 页概述 2021 年论文，附录第 87–90 页收录全文。

## 阅读结论

1. **先准确建图。** 官方给出 SRB 内部 Arc、SRB 间 Net 的连接及延时，以及 Gap/Block 等特殊区域。应先明确端口方向、跨 SRB 位移和特殊区域的语义，再做优化。不能直接把 FPGA 预测论文中的几何距离当成最短路径答案。
2. **先做精确基线。** 将可用 Port 作为节点、Arc/Net 作为带非负权的有向边，用 Dijkstra 算法计算小批量请求的精确答案；这也是后续近似模型的校验基准。
3. **大量查询需要预处理。** Marquardt 的按 `(dx,dy)` 查表思路适合规则区域的快速基线，但本题存在 Gap/Block、端口类型和方向差异，单纯位移表无法保证精确。Goldberg–Harrelson 的 ALT 地标下界可用于精确 A* 加速，但每次仍要搜索；是否足够快须按官方数据评估。
4. **学习模型只作为候选校正层。** Martin 论文用 20 项特征和随机森林预测布线后的 net delay，测试集 `R²=0.948`，较静态模型的 `R²=0.780` 更好；这是论文任务的指标，不等于赛题准确率。论文中的特征包括 fanout、HPWL、拥塞、资源跨越与静态延时。赛题的图结构和 2 GB 内存、单线程、10 亿次查询限制使其不能原样搬用。
5. **最近的 FPGA 工作可帮助特征设计。** TD-Placer 论文列出 25 项特征，包含横纵距离、扇出、局部密度、跨异构资源及网络拓扑。对本题应只选官方 JSON 能计算、且预处理后查询成本低的特征。

## 下一步技术判断

拿到官方五个 JSON 和公开测试集后，先统计节点/边数、连通性、延时是否非负、请求端点分布和重复率，再决定采用端点缓存、分区距离表、地标方法或近似模型。任何预处理方案都必须核算 2 GB 内存与单线程 10 亿次查询的总时间；目前没有足够数据宣称哪种方法最优。

更新：官方数据现已获取，已完成全量文件审计与小批精确最短路核对。当前进展、论文到实验的映射和验收条件统一维护在 [实施计划](../docs/PLAN.md) 与 [阶段报告](../reports/BASELINE.md)。

## 后续可读的最短路论文

这些论文比前述 FPGA 布局论文更贴近赛题的海量两点查询，但实验对象主要是道路网络，算法效果不能直接套用到 SRB 图。

1. Geisberger et al., [*Contraction Hierarchies: Faster and Simpler Hierarchical Routing in Road Networks*](https://ai.dmi.unibas.ch/research/reading_group/geisberger-et-al-wea2008.pdf), WEA 2008：预处理时收缩节点并添加保持最短路的捷径；查询使用双向分层搜索。重点关注捷径数量是否适合 2 GB 内存。
2. Abraham et al., [*A Hub-Based Labeling Algorithm for Shortest Paths on Road Networks*](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/05/hl-sea.pdf), SEA 2011：为节点预存枢纽距离，查询时取两端标签的交集；适合追求极低查询延迟，但标签大小可能成为瓶颈。
3. Arz, Luxen, Sanders, [*Transit Node Routing Reconsidered*](https://arxiv.org/abs/1302.5611), 2013：预处理全局通行节点和局部入口，做快速精确距离查询；需要额外处理局部查询。
4. Bast et al., [*Route Planning in Transportation Networks*](https://arxiv.org/abs/1504.05140), 2015：综述预处理时间、空间与查询时间的取舍，适合确定本题的候选路线。

`Optimal Approximate Distance Oracle for Planar Graphs` 等平面图结果只有在确认 SRB 的 Port/Arc/Net 图满足相应平面性和权重假设后才适用，不能仅凭 120×550 的网格坐标套用。

## V8 新增参考：压缩路径数据库

Botea, Harabor, *Path Planning with Compressed All-Pairs Shortest Paths Data*, ICAPS 2013。
[作者公开 PDF](https://pathfinding.ai/pdf/botea-harabor-icaps13.pdf)，本地文件 `Botea_Harabor_2013_Compressed_Path_Data.pdf`。

阅读重点：预处理最短路径并压缩下一步动作，利用空间相邻目标的共同动作减少存储。其全点对路径预处理和无损压缩思想属于已有工作，不能作为我们的原创。V8 借鉴预处理与压缩的工程思想，存储 FPGA 规则区域的局部可行路径延时及足迹证书，以平移后的有效性检查获得上界；与完整全点对最短距离数据库不同。具体创新候选和限制见 `reports/V8-path-witness-research.md`。

## V9–V14 新增参考：架构自适应的路由前瞻

Petelin, Betz, *The Speed of Diversity: Exploring Complex FPGA Routing Topologies for the Global Metal Layer*, FPL 2016。
[作者公开稿](https://www.eecg.utoronto.ca/~vaughn/papers/fpl2016_complex_routing.pdf)，已下载 `Petelin_Betz_2016_Complex_Routing.pdf`。重点阅读第 II-D 与 IV-D 节及图 4：从少量参考导线运行按延时排序的 Dijkstra，并按导线类型、方向和相对位移建立路由前瞻表。

该文说明导线类型、连接拓扑和长导线入口对延时估算的重要性；这些基本思路已有研究依据。本项目新增候选集中在逐端口可行路径的平移证书、入口路径银行、可重复长导线组合，以及由有效上界约束学习模型。前瞻估计与本题的最短路标签、逐条误差评分任务不同，不能把论文结论直接当成本题性能。现代 [VTR 路由前瞻文档](https://docs.verilogtorouting.org/en/latest/api/vprinternals/router_lookahead/) 可用于核对已有实现概念。

## 2026-10-05 新架构参考（已下载，已阅读相关方法章节）

| 论文 | 本地 PDF | 本轮用途 |
|---|---|---|
| [CatBoost (NeurIPS 2018)](https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html) | `CatBoost_2018.pdf` | 类别端口/端口对模型对照 |
| [Revisiting Deep Learning Models for Tabular Data (2021)](https://arxiv.org/abs/2106.11959) | `Tabular_DL_2021.pdf` | 表格残差神经网络参照 |
| [Min-Max-Plus Neural Networks (2021)](https://arxiv.org/abs/2102.06358) | `Min_Max_Plus_NN_2021.pdf` | 结构化 min/max-plus 学习思路 |
| [Min-plus algebraic low rank matrix approximation (2017)](https://arxiv.org/abs/1708.06552) | `Min_Plus_Low_Rank_2017.pdf` | 潜在路线和距离分解 |
| [Transit Node Routing Reconsidered (2013)](https://arxiv.org/abs/1302.5611) | `Transit_Node_Routing_2013.pdf` | 长线中转节点、入口/出口分解 |

方法差异、实际实验与创新边界见 [V20–V35 研究报告](../reports/V20-V35-architecture-research.md)。不能把参考论文的基础方法宣称为我们的原创。

## 2026-10-05 周期下界与误差控制搜索

新增并阅读相关方法章节：

- `Culberson_1998_Pattern_Databases.pdf`：[作者公开稿](https://webdocs.cs.ualberta.ca/~jonathan/publications/ai_publications/compi.pdf)，抽象问题距离与可采纳下界。
- `Felner_2004_Additive_PDB.pdf`：[论文](https://arxiv.org/abs/1107.0050)，代价分解；当前实现方向下界取最大，并非复现可加PDB。
- `Anytime_Heuristic_Search_2007.pdf`：[论文](https://arxiv.org/abs/1110.2737)，解质量界与持续改进。
- `Bidirectional_Bounded_Search_2025.pdf`：[论文](https://arxiv.org/abs/2511.10272)，双向有界搜索参照。

V40按官方架构构造周期模式下界，完整验证99.9963756；算法区别、证明条件和失败路线见 [V36–V40报告](../reports/V36-V40-precision-research.md)。
