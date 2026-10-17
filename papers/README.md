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

## V99 新架构探索：张量与多尺度编码（2026-10-07）

已下载 PDF 和作者公开 HTML，阅读分解形式、初始化、训练及局限相关章节：

- [Si 等，An efficient tensor regression for high-dimensional data](https://arxiv.org/abs/2205.13734)，`Si2024-tensor-regression.pdf`。参考六维离散残差的 TT 核矩阵连乘表示。原文采用带正交结构的回归及黎曼优化；本轮原型使用加权绝对误差与 Adam，并非完整复现其算法或理论保证。
- [Yin 等，TT-Rec (MLSys 2021)](https://arxiv.org/abs/2101.11714)，`Yin2021-TTRec.pdf`。参考秩、存储、计算的共同权衡及乘积初始化问题。原文主要面向推荐模型及加速器；本题不会直接继承其压缩比例和加速结论。
- [Müller 等，Instant Neural Graphics Primitives with a Multiresolution Hash Encoding (SIGGRAPH 2022)](https://arxiv.org/abs/2201.05989)，`Mueller2022-hash-encoding.pdf`。参考多尺度可学习编码与小网络消歧。本轮采用离散端口和位移联合哈希，没有原文空间网格的多线性插值、CUDA融合内核，因此称为借鉴原型，不称论文复现。

所有新拟合仅使用 development；validation 用于比较，未读取 holdout。项目创新候选是 FPGA 周期相位、端口耦合、实际边界表征和压缩残差的组合，不能将 TT 或多尺度哈希本身宣称为原创。具体结果和限制见 V99/V100 实验报告。

### 请求流水线与内存访问

- Kocberber, Falsafi, Grot (2015), *Asynchronous Memory Access Chaining*, PVLDB 9(4),252–263. [官方论文](https://www.vldb.org/pvldb/vol9/p252-kocberber.pdf)，已保存Kocberber2015-AMAC.pdf。本轮读取内存延迟隐藏与方法第2/3节：静态批次适合规则查询，独立状态调度可处理不同访问链长度。V113先试验分阶段批量预取，尚未复现完整AMAC调度；论文的数据库加速比例不能直接用于本题。

## V123：稀疏路线交互的低秩模型

Blondel, Ishihata, Fujino, Ueda (2016), *Polynomial Networks and Factorization Machines: New Insights and Efficient Training Algorithms*. [作者论文](https://arxiv.org/abs/1607.08810)，已下载 `Blondel2016-Polynomial-Factorization.pdf`。阅读第2.2及3节的二阶特征交互、低秩参数化与ANOVA表达。V123仅借鉴二阶FM表达，使用AdamW及赛题评分损失；没有复现论文的坐标下降/多凸训练算法，也不继承其理论或其他任务性能。路线特征来自估算器，标签仅来自development；原型泛化未达到阶段目标。

## V132：面向联合目标的新检索（2026-10-07）

新增本地PDF：Akiba2013-Pruned-Landmark-Labeling.pdf（SIGMOD2013，阅读标签查询/剪枝/有向带权扩展）；Alabi2019-Learning-to-Prune.pdf（阅读任务假设和探索/利用剪枝）。另通过网页读取CRP2011与HHL2012的相关方法部分，本地下载分别403/超时。KFL2021只阅读Google作者页与官方代码，PDF403，未通读全文。文献、下载状态、适配限制与三个新架构的执行顺序见 [V132研究计划](../reports/V132-literature-and-new-architectures.md)。不将既有两跳标签、分区覆盖图、KFL或学习剪枝方法本身作为原创。

## 2026-10-07 V145–V147 长距离尾部诊断

Nowak & Charron-Bost (2014), An Overview of Transience Bounds in Max-Plus Algebra. 原始PDF：https://arxiv.org/pdf/1405.3458；本地Nowak2014-MaxPlus-Transience-Overview.pdf，214323 bytes，SHA256 bfa2d4b43247d6f30986ab3137ec69f284c465d6b81023d76fa4e1a585cd2290。已读引言、§2定义/最终周期定理和文章结构，未通读证明。论文矩阵幂参数是路径边数；赛题参数是位移，须先建立正确状态转换，不能直接套用定理保证第6或20周期后稳定。仅作为“区分暂态和稳定尾部”的研究参考。

V142端口乘积交互另参考Rendle2010 Factorization Machines：作者项目https://www.libfm.org/已核实；官方PDF链接超时，未宣称下载或全文阅读，表达方式为启发式适配。

## V163：由精确算法提供监督

- Hinton, Vinyals & Dean (2015), Distilling the Knowledge in a Neural Network：[原文](https://arxiv.org/abs/1503.02531)，本地 `Hinton2015-Knowledge-Distillation.pdf`，SHA256 `74e6689115c539db499f9d6153edecb364059926fd45402454f8210442444c5a`。已读引言与第2节，未通读实验。借鉴教师与部署模型分工；延时回归没有采用其分类温度 softmax。
- Veličković et al. (ICLR 2020), Neural Execution of Graph Algorithms：[原文](https://arxiv.org/abs/1910.10593)，本地 `Velickovic2020-Neural-Graph-Algorithms.pdf`，SHA256 `493bc68a8cbae3d7d0daf510ce0e14abb8d5b50c67c2fbcc8ceab437b25d5566`。已读引言与第2节；借鉴图算法监督思想，尚未复现逐步消息传递网络。

具体适配与实验边界见 `reports/V161-V163-accuracy-direction.md`。

## V198追加CPD参考与阅读范围（2026-10-08）

- Botea, *Fast, Optimal Pathfinding with Compressed Path Databases*, SoCS2012：[论文PDF](https://ojs.aaai.org/index.php/SOCS/article/download/18251/18042/21767)，本地Botea_2012_Fast_Optimal_Pathfinding_CPD.pdf。已读两页方法说明：Dijkstra生成首动作、同动作空间矩形压缩、在线逐步提取。预处理动作与路径相干性属于已有方法。
- Zhao等, *Bounded Suboptimal Path Planning with Compressed Path Databases*, ICAPS2020：[论文PDF](https://ojs.aaai.org/index.php/ICAPS/article/download/6678/6532/9907)，本地Zhao_2020_Bounded_Suboptimal_CPD.pdf。已读引言、centroid误差定理与构建/反向CPD方法，未通读所有实验及证明。其2δ路径界使用无向网格条件，FPGA有向端口不能直接继承；可参考选择目标子集和反向压缩，效果仍需验证。
- Botea、Strasser、Harabor, *Complexity Results for Compressing Optimal Paths*, AAAI2015：[作者PDF](https://pathfinding.ai/pdf/sbh-aaai15.pdf)，本地Botea_Strasser_Harabor_2015_CPD_Complexity.pdf。仅读摘要与引言；涉及最优RLE列排序的困难性，不声称已阅读完整证明。

三个本地文件均核对PDF标识和SHA256，见reports/V198-cpd-literature-downloads.json。V193/V196物理Bellman差字段是当前实验设计，不宣称新基本图算法，也不宣称已达联合目标。
