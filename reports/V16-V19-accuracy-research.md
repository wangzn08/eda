# V16–V19：精度优先研究

日期：2026-10-05。按用户要求，先提高验证分；本轮未重新开展最终留出评分、十亿条测速或提交包验收。

## 结果

**当前 C++ 最好验证分为97.40821522441175，较V14的97.22350366143732增加0.184712分。** 1536棵树、127叶的结构规模与V14相同；树字节码仍为3,110,400字节。C++与Python在150,053条验证请求上的预测逐条相同。尚未达到99.9，也未证明正式吞吐达标。

| 候选 | 验证分 | 结论 |
|---|---:|---|
| 原V14 | 97.223504 | 保留对照 |
| V16：联合导线余数、周期位置、端点交互与相对误差加权 | 97.224905 | 提升极小，模型更大，不采用 |
| V16加新路径上界修正 | 97.356375 | 低于原模型配新路径 |
| V17：短/中距离专门模型（基于V16配新路径） | 97.356418 | 未超过当前候选，不采用 |
| V18：原模型加扩展可行路径枚举 | 97.359238 | 已接入可选参数 |
| V19：用扩展路径上界特征重新训练 | **97.408215** | 已导出并接入C++可选算法 |

V16同时改变了特征、加权方式及部分训练参数，因此结果不能单独证明某个新增特征无效。V17以距离<150为分流条件，只使用输入属性；其基准是V16配新路径修正，不是最终选中的V18。所有参数选择均使用固定验证集，反复选择会有验证集选择偏差，本轮未开启留出集。

## 先定位误差

原V14的低估73,730条、高估69,730条，简单整体加减偏置缺乏依据。

- 中等距离（曼哈顿距离25–149）51,427条，占34.27%；该组得分95.75795，贡献52.36%的总扣分。
- 长距离（>=150）96,024条，该组得分98.00927。
- 无有限上界8,379条，仅贡献7.29%的总扣分。即使将其全部修到满分，总分也最多增加约0.20236分，因此只扩大覆盖范围不足以实现99.9。

明细：[误差诊断](V16-error-diagnosis.json)。诊断只读取验证集；训练始终仅使用700,705条开发数据。

## 有效的路径改动

原长导线组合只枚举第一段的floor(remaining/span)和其加一值，第二段也采用类似枚举。局部尾部能覆盖12格，因此对于部分余数，少走一段长导线、再用局部路径补齐，也是合法且可能更短的路径。V18加入这一候选，仍保留原候选和所有边界、Block、Gap与路径足迹有效性检查。

- 39,058条验证请求的可行上界降低。
- 上界恰等于最短延时的请求由12,860条增至15,114条。
- 4,744条V14预测被更紧上界修正，完全匹配由6,593条增至7,936条。
- 与验证golden比较，没有发现上界低于最短延时的情况。
- 另尝试多走一段再回接，只额外降低2条上界，评分无提升、耗时增加，因此不保留。

合法可行路径长度U满足最短距离D<=U。对原预测P取min(P,U)：P<D时不改变；P>=D时误差不增。这个结论依赖路径证书正确，不意味着所有请求都已得到精确最短路。

V18保留旧上界作为原模型特征，只在预测后作新路径修正，以避免改变原模型输入。V19则用新增枚举得到的更紧上界重新生成四项上界特征，保持V14的主要训练参数：L1、1536轮、127叶、最小叶样本40、学习率0.05、相同随机种子。

## 当前V19指标

- 验证分：97.40821522441175。
- 完全相等：7,334 / 150,053。少于V18的7,936，但连续误差评分更高；不能以完全匹配条数替代官方评分。
- 相对误差中位数：0.39604%；P95：2.04953%；P99：4.11429%。
- 最大相对误差仍为56.31%，说明极端难例尚未解决。
- C++单线程验证运行约7.4秒CPU；这只是该规模测量，不是十亿条性能验收。
- 树字节码3.11MB；本轮未重新打包核算整个新候选提交大小。既有V14压缩包仍是V14，不代表V19。

## 方法依据与创新边界

1. Petelin & Betz, *The Speed of Diversity: Exploring Complex FPGA Routing Topologies for the Global Metal Layer*, FPL 2016：按导线类型、方向与相对位移建立架构前瞻，是考虑长导线入口、方向和周期性的依据。[论文笔记](../papers/README.md)
2. Botea & Harabor, *Path Planning with Compressed All-Pairs Shortest Paths Data*, ICAPS 2013：预处理与压缩路径数据已有研究依据。[论文笔记](../papers/README.md)
3. Martin et al., *A Machine Learning Approach to Predict Timing Delays During FPGA Placement*, 2021：为架构/几何特征结合学习模型提供参考；其任务、指标与本题不同。[论文笔记](../papers/README.md)

联合余数特征、L1加权、分组训练都是常规建模手段；补全跳数枚举也属于具体算法改进，不能据此声称首创。项目可进一步研究的贡献是带平移有效性证书的路径组合，以及如何用这些架构约束减少学习模型误差。本轮证明了该方向的实际收益，未证明达到精确距离或99.9。

## 复现与下一步

研究环境依赖记录于`scripts/requirements-research.txt`。固定数据划分和既有V14特征/上界需已准备。

```sh
out/research-env/bin/python scripts/analyze_v14_errors.py
out/research-env/bin/python scripts/experiment_v16_lattice.py
out/research-env/bin/python scripts/experiment_v18_hop_window.py
out/v18/cycle_oracle_apply out/evaluation/development.v13-bound.csv out/evaluation/development.v18-bound.csv out/local-oracle/long-tail-12-dict.bin
out/research-env/bin/python scripts/experiment_v17_distance_expert.py
out/research-env/bin/python scripts/experiment_v19_route_bound.py
out/research-env/bin/python scripts/export_v19_tree.py
make -j1
out/research-env/bin/python scripts/evaluate_v19_cpp.py
```

直接使用V19：

```sh
build/estimate -in requests.csv -out results.csv --algorithm v19-tree --local-oracle out/local-oracle/factorized-20-planes.bin --cycle-oracle out/local-oracle/long-tail-12-dict.bin
```

仓库默认仍是V6，需要显式选择V19。下一步优先分析新候选残余误差对应的多次转向、跨Block与尾部路径不足，研究更完整的路径组合；本轮证据不支持仅靠增加树数量推进到99.9。

原始记录：[V16](V16-lattice-research.json)、[V17](V17-distance-expert.json)、[V18](V18-hop-window.json)、[V19训练](V19-route-bound-research.json)、[V19 C++](V19-cpp-validation.json)。
