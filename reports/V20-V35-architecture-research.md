# V20–V35：跨架构精度研究（2026-10-05）

## 本轮结论

本轮比较类别模型、残差神经网络、潜在路线 min-plus 分解、周期相位张量、入口/出口分解、路线搜索和自适应精确求解。模型在 development 700,705 条拟合，固定 validation 150,053 条选型；没有读取独立 holdout。反复选型会使验证结果偏乐观，以下不是官方隐藏集成绩。

- V19 原 C++ 验证分 **97.408215**。
- V30 神经路线组合 + 有证书的宏路径上界，C++ **97.952110**。
- V35 在 V30 上增加按输入距离和模型分歧触发的精确 A*，首轮完整 C++ **98.387821**。
- 99.9 尚未达到。分数是官方相对误差变换的平均值，不是答案完全相同的百分比。

完整数字、逐条对齐及资源见 [V35 机器报告](V35-adaptive-validation.json)。固定候选源码仍保留 V6 默认入口；研究候选必须指定参数。

## 架构对照

所有神经模型表中的分数包含对应报告指定的 V19 融合权重，不能解释为独立神经网络成绩。V30/V35 还包括路径约束或精确回退。

| 方法 | 验证分 | 判断 |
|---|---:|---|
| V19：1536 棵残差树 + 路径上界 | 97.408215 | 本轮出发点 |
| V20：类别特征 CatBoost，深度 6 | 97.400682 | 模型约 108 MB；另一深度配置提前停止 |
| V29：受限类别统计 CatBoost，深度 8 | 97.401652 | 约 6.20 MB，仍未超过 V19 |
| V21：端口嵌入 + 谱图嵌入 + 残差 MLP | 97.517132 | 有改善 |
| V23：扩大 MLP 宽度、深度及训练轮数 | 97.512633 | 更大模型没有更好 |
| V24：64 条潜在路线的 softmin 分解 | 97.679817 | 比直接回归更适合本题 |
| V26：物理下界以上的路线余量模型，128 路线 | 97.653578 | 单独稍低，与 V27 互补 |
| V27：端口 × 横纵周期相位 × 路线的低秩张量 | 97.839650 | 最好的单个神经候选融合 |
| V28：16 入口 × 16 出口的运输矩阵分解 | 97.553615 | 本轮未采用 |
| V31：周期张量扩大到 128 路线 | 97.724043 | 加容量仍未超过 64 路线 |
| V30：V27 75% + V26 25% + 宏路径搜索，Python | 97.952108 | 采用 |
| V30：同组合，标准 C++ 输入输出 | 97.952110 | 与 Python 存在极少数 1 ps 舍入差异 |
| V35：增加短距离及分歧请求精确求解，C++ | 98.387821 | 当前精度候选 |

其余消融保留在 V20–V31 的 JSON 中，包括宏路径预算 256/1024/4096/16384/65536。不能把不同负载下的时间直接用于预算间速度比较。

## 方法和创新边界

### 1. 潜在路线分解代替单一延时回归

路线 k 的成本由源端口项、目标端口项和几何项组成，训练时用稳定 log-sum-exp 的 softmin 组合。V27 再加入端口低秩因子与横向模 10、纵向模 12 的余数相位交互，学习长线跳数留下的周期误差。固定谱图嵌入只使用官方 Arc/Net，不使用答案。

这 64 条是**学习得到的潜在模式**，不是已证明存在的实际走线路径。因此神经网络预测不能用作精确搜索的安全上界。

### 2. 下界、真实路径上界和模型联合

下界来自四组端口折叠图势函数。对每条边扣除最大可能的几何势增长，在折叠图上计算最短距离；势差沿路线相消，得到实际图距离的下界。横向采用压缩坐标 φ(x)=x−clip(x−76,0,14)，适配官方可横穿区域；另外加不可避免的 LineGap 跨线延时。

证明依赖官方架构：不存在可纵向跳过的 Block，可横穿 Block 的列范围为 76..89；Python 生成过程检查这个条件。架构变更需要重新推导和生成，不能把常量表用于任意 FPGA。

宏路径搜索以 32 类长线输入端口为中间节点，组合已有入口路径银行、实际 Arc+Net 和精确局部尾部。每一步检查平移路径的边界、Block 和 LineGap。允许多次转向；预算耗尽时返回目前找到的真实路径成本 U。它只搜索完整图的一部分，因此 U 是可行上界，通常不等于最短路。

### 3. 模型分歧驱动精确回退

V35 的条件在看答案之前即可由输入和预测计算：

- 端点原始 Manhattan 距离 < 25；或
- 两个融合神经候选的 |p1−p2| / max((p1+p2)/2,1) > 1%。

触发后在包含所有官方 Arc+Net 的压缩输入端口图上运行 A*，使用上述下界和**有实际路径证书的 U**剪枝。不以神经预测值剪枝。未触发的请求使用 V30。

验证中短距离触发 2,602 条，其他分歧触发 9,444 条，共约 8.03%。分别独立输出与标准答案核对，12,046 条均完全一致；2602 条短距离还与原精确 compressed 求解器一致。这个结果支持当前数据上的实现正确性，不能代替任意架构的证明。

### 可作为我们的研究贡献候选

- 面向官方端口和长线周期的路线相位张量，而非只扩大通用模型。
- 路径证书上界、端口势下界与学习型路线估计联合。
- 用两个结构不同的模型分歧决定是否付出精确搜索成本。

min-plus、低秩分解、神经网络、TNR 和 A* 都是已有方法。以上组合与领域适配仍需进一步消融、独立评估和查新，不能宣称首次提出这些基础算法。

## C++ 实现与资源

- 训练使用本机 PyTorch MPS；推理是 C++17 单线程，不依赖 Python、PyTorch 或 GPU。
- 选定的两个原始 float32 权重在 `models/`，合计 **2,055,836 bytes**；校验和见 [权重导出记录](Neural-route-export.json)。没有保存验证答案表。
- V30 完整 150,053 条：CPU **82.447 s**，最大 RSS **297,992,192 bytes**。
- V35 首轮完整 150,053 条：CPU **356.58 s**，最大 RSS **866,664,448 bytes**。
- V35 增分很大一部分来自精确回退，不能说神经模型自身达到 98.3878。
- 本轮没有正式打包验收、独立 holdout 或十亿请求测试；已知独特请求耗时离正式要求很远。下一阶段要减少搜索量和推理开销，不能靠重复请求缓存的成绩证明隐藏集达标。

消除同请求内重复的第二模型和教师计算后，完整复跑 CPU **346.566 s**，最大 RSS **869,203,968 bytes**，与首次输出逐字节相同。只取得小幅提速，不代表满足正式吞吐要求。

## 复现入口

先使用已有官方数据和路径资产：

```sh
make -j1
build/estimate -in out/evaluation/validation.request.csv \
  -out out/evaluation/validation.v35-optimized.csv \
  --algorithm v19-tree \
  --local-oracle out/local-oracle/factorized-20-planes.bin \
  --cycle-oracle out/local-oracle/long-tail-12-dict.bin \
  --neural-model models/phase-route.bin \
  --neural-model-second models/interval-route.bin \
  --neural-second-weight 0.25 --macro-budget 65536 \
  --exact-short-distance 25 --exact-uncertainty 0.01
```

去掉最后两个参数是 V30 预测组合。训练脚本 `experiment_v21_neural.py`、`experiment_v24_minplus_neural.py`、`experiment_v26_interval_minplus.py`、`experiment_v27_phase_tensor.py` 等记录架构与训练设定；`export_route_neural_models.py` 导出选定权重。`prepare_adaptive_references.py` 按输入和冻结预测生成短距离/分歧参考请求；使用 `--algorithm compressed --exact-astar` 分别输出到 `validation.v34-short-astar.csv`、`validation.v34-uncertain-exact.csv`，短距离另用原 `--algorithm compressed` 输出到 `validation.v33-short-exact.csv`。`evaluate_adaptive_architecture.py --prediction validation.v35-optimized.csv --log v35-optimized.log` 核对端点顺序、独立精确结果和评分，只允许当前固定 validation。

## 参考文献与方法对应

以下五份 PDF 已下载，已阅读摘要及相关方法章节；本轮没有声称逐字通读全部论文。

1. Prokhorenkova et al., **CatBoost: unbiased boosting with categorical features**, NeurIPS 2018：[官方论文](https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html)。V20/V29 类别学习对照。
2. Gorishniy et al., **Revisiting Deep Learning Models for Tabular Data**, NeurIPS 2021：[论文](https://arxiv.org/abs/2106.11959)。V21/V23 的表格残差网络参照；没有复现其 FT-Transformer。
3. Luo & Fan, **Min-Max-Plus Neural Networks**, 2021：[论文](https://arxiv.org/abs/2102.06358)。min/max-plus 运算的结构化学习思路；我们的 softmin 路线模型并非该论文原网络。
4. Hook, **Min-plus algebraic low rank matrix approximation**, 2017：[论文](https://arxiv.org/abs/1708.06552)。距离矩阵的 min-plus 分解启发 V24/V28。
5. Arz, Luxen & Sanders, **Transit Node Routing Reconsidered**, 2013：[论文](https://arxiv.org/abs/1302.5611)。入口/出口和长距离中转节点思路；我们的有预算宏路径上界并非完整 TNR 算法。
6. Goldberg & Harrelson, **Computing the Shortest Path: A* Search Meets Graph Theory**, 2005：已有本地论文和 [既有阅读笔记](../papers/README.md)。势函数下界与 A* 思路的依据；当前势表来自端口折叠图，未直接复现 ALT 地标。

## 下一阶段可量化目标

1. 在保留 V30/V35 冻结模型的基础上，测出未触发精确回退的误差集中在哪些端口、周期和障碍情形。
2. 用更多局部精确路径模式改进宏搜索覆盖，优先替代当前代价高的精确回退。
3. 训练专门的误差/搜索收益预测器，并以受限 CPU 预算的精度曲线选择回退条件；门控训练和评估继续分离。
4. 在用户要求验收时再冻结方案并使用未参与选型的 holdout；持续查看 validation 不能证明达到隐藏集 99.9。
