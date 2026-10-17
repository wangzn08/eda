# V132：针对99.5分与600秒联合目标的文献筛选

日期：2026-10-07。当前合格基线V116验证99.0256649430、两轮十亿CPU本机外推684.0975/689.4150秒。目标未完成。本文提出研究假设，不报告新架构已经达标。

## 检索与阅读范围

只采用作者、会议、官方实现等一手来源。下载状态和阅读程度分开记录。

| 文献 | 本轮已阅读的内容 | 保存状态 | 适配限制 |
|---|---|---|---|
| Akiba, Iwata, Yoshida, *Fast Exact Shortest-Path Distance Queries on Large Networks by Pruned Landmark Labeling*, SIGMOD2013, https://arxiv.org/abs/1304.4661 | §3.3、§4剪枝与标签交集、§6有向/带权扩展 | papers/Akiba2013-Pruned-Landmark-Labeling.pdf，HTML另存out/v132/pll.source | 带权必须用Dijkstra；原文明确位并行BFS标签不能用于带权图。完整两跳覆盖才保证精确，小标签子集不自动精确。 |
| Delling, Goldberg, Pajor, Werneck, *Customizable Route Planning*, SEA2011, https://www.microsoft.com/en-us/research/wp-content/uploads/2011/05/crp-sea.pdf | §3分区、边界入口/出口、覆盖图、骨架稀疏化与多层矩阵 | 网页工具读取12页PDF；本地下载403，未谎称已下载 | 保留所有必要边界状态并准确计算区域内距离才能保持精确；论文查询使用并行，不能继承为本题单线程速度。 |
| Abraham, Delling, Goldberg, Werneck, *Hierarchical Hub Labelings for Shortest Paths*, ESA2012, https://www.microsoft.com/en-us/research/wp-content/uploads/2012/04/MSR-TR-2012-46.pdf | §2有向前向/反向标签和最短路覆盖条件 | 网页工具读取15页PDF；本地下载超时 | 道路图的小标签并不保证FPGA图也小；全芯片逐节点标签可能远超100MB。 |
| Morioka, Louidor, Bakst, *Monotonic Kronecker-Factored Lattice*, ICLR2021, https://research.google/pubs/monotonic-kronecker-factored-lattice/ | 官方作者页摘要、TensorFlow Lattice官方实现的插值乘积、尺度初始化及约束 | 官方代码out/v132/kfl-code.source；PDF验证页403，未通读全文 | 仅借鉴乘积分段线性表达；相位、端口和跨障碍延时不保证全局单调，不能强行添加单调约束。 |
| Alabi et al., *Learning to Prune: Speeding up Repeated Computations*, 2019预印本, https://arxiv.org/abs/1904.11875 | §2任务假设、§3探索/利用剪枝、最短路实例 | papers/Alabi2019-Learning-to-Prune.pdf，HTML out/v132/prune.source | 原文最短路场景固定s/t而改变边权，本题固定边权而改变端点。只能借鉴剪枝思路，不移植原理论保证。 |

KFL官方实现：https://github.com/tensorflow/lattice/blob/master/tensorflow_lattice/python/kronecker_factored_lattice_lib.py 。VTR官方说明还确认compressed_map通过稀疏采样减少构建时间和内存，但它是前瞻估计，不是精确距离保证：https://github.com/verilog-to-routing/vtr-verilog-to-routing/blob/master/doc/src/vpr/command_line_usage.rst 。

## 从现有证据出发

V117误差分析：低估占总评分损失约70%；跨障碍请求55123条，贡献0.4621评分点损失。增加候选后直接取最小值未必改善主导误差。V125/V131纠偏全验证99.21014，但孤立C++模型推理外推约13725秒/十亿，远超600秒。V127–130周期方案与基线的标签依赖选择上限99.30225，因此单靠这批候选的门控不能达到99.5。

V116本身已超过600秒，故“在现有版本上增加少量昂贵回退”没有自动可用的时间余量。必须先减少基础查询成本，或用新的快速主模型替换一部分流程。不能把一个版本的精度与另一个版本的速度拼在一起。

## A：小型插值乘积纠偏（首个原型V133）

表达为 route_bias + Σ_r scale_r × source_factor_r × target_factor_r × Π_d interpolated_curve_rd(x_d)。每个数值特征只在相邻两个结点之间插值，端口身份用独立类别系数，避免把端口编号当连续数值。以少量乘法和数组读取取代数百棵树的随机节点跳转。

首轮rank2/4/8、6个数值特征、8结点、按路线类型/位移方向分组；数值特征来自周期数、候选余量、四带基值曲率、横向与交互修正。缺失路线描述使用单独类别。只用development拟合赛题tanh损失；不对端口编号/位移/相位强制单调。validation只比较，holdout不读。参数量预计很小，但查询时间需C++测量，不以参数字节数替代速度。

这与先前二阶FM不同：含可学习的分段线性曲线及高阶乘积；与TT原型不同：不做连续核心矩阵连乘。乘积分解本身已有KFL/CP依据，不宣称原创。首轮是受文献启发的适配，不是完整复现单调KFL论文。

晋级要求：全验证优于V116，并在原生整程序中表现出可接受成本。若rank增加主要提升development而validation不涨，停止堆秩。若全验证未优于基线，则不部署。

## B：真实端口边界骨架＋局部两跳标签

将芯片按普通区、障碍边界和重复条带划分。为区域内真实入口/出口端口预计算受该区域约束的最短距离，以保距捷径形成小骨架；在骨架上建立前向/反向两跳标签。查询为源点局部接入、骨架距离、目标局部退出的组合。

相较V122固定几何枢纽，该方案保留多个实际端口、方向和区域内连接代价。跨障碍的入口兼容性成为结构信息，而不只用一个ILE0点代替所有路线。可探索对重复区域共享标签拓扑，并只存边界附近差值。

先做结构/空间审计：候选入口数、边界弧数、骨架捷径数、平均/最大标签长度及预计总字节。首个局部图必须核对原图距离。完整边界状态太大时，研究稀疏覆盖＋已有基线回退，但明确失去全局精确保证。不得先构建全芯片逐节点标签；也不能凭二维坐标套用平面图理论。

优先针对跨障碍损失最大的结构区。基础数学来自CRP/Hub Labeling；本题的周期共享、真实端口边界与差值压缩组合是待验证的贡献候选。先查现有实现与文献，不能宣布世界首次。

## C：按请求剪枝＋代价预算分配

给不同请求分配1/2/4/8源候选及是否启用局部纠偏，用端口族、位移相位、边界关系等低成本结构特征选择。拟合目标同时惩罚评分损失和实际CPU成本，不单训练“残差是否大”。development内部另划训练/选择子集确定阈值，再固定门控比较完整validation。

选择候选子集通常是不保证精确的近似优化；必须记录漏掉最佳候选造成的降分。若要证明剪枝安全，需要相应候选的有效下界和真实可行上界。V116的近似最小值不是可行路径上界，不能拿它作安全A*剪枝证据。原论文的在线随机探索不直接用于提交，保持输出确定性与无请求结果缓存。

## 执行顺序

1. 完成V133小型插值模型的development拟合和全validation比较，保留全部rank/epoch结果。
2. 对晋级模型做原生输出一致性及模型成本筛选；只有整程序时间才用于联合目标判断。
3. 边界骨架先审计入口/出口规模，在小区域实现与原图距离比较，再决定是否扩展。
4. 候选门控单独测调用比例、评分损失和节省CPU；需要基础吞吐先降到600秒内，并为纠偏留预算。
5. 最后同一冻结版本全验证及两轮千万请求实测，初始化计一次，100MB/2GB核对。没有新结果时保留V116。

## V133首轮结果（已完成）

rank2/4/8各24轮，全部9个检查点均在150053条完整validation上比较。最佳rank8/epoch24为99.0593207240，参数float32共60,608 bytes；rank4最佳99.0555962713，参数30,368 bytes；rank2最佳99.0508289023，参数15,248 bytes。只在development拟合，缺失描述类别单独映射，不读holdout。MPS仅用于研究训练，不代表提交使用GPU。结果见 reports/V133-factored-lattice.json，代码 scripts/experiment_factored_lattice.py。

这证明小型插值表达能略微纠偏，但还没有达到99.5，也未完成C++/端到端速度测量，不能声称联合目标改善。相较深树99.21014，精度优势尚未成立。后续应先判断误差是特征缺失还是表达不足；避免只增加rank。真实端口边界骨架仍是独立、尚未实施的研究路线。
