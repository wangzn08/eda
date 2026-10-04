# V8：带平移有效性证书的局部路径上界

## 本轮目标与状态

遵循当前优先级：持续提升固定验证集评分，暂不开展提交验收、隐藏集评估和十亿请求测速。研究分支的高精度候选达到 95.04105535616392；这是公开数据划分中的验证分，不是完全匹配率，也不是官方最终成绩。默认快速路线叠加同一模块达到 94.3100060336682。

## 参考与创新边界

- Marquardt, Betz, Rose (2000), Timing-Driven Placement for FPGAs：以位移预计算延时表，提供规则 FPGA 区域预处理思路。
- Martin, Grewal, Areibi (2021), A Machine Learning Approach to Predict Timing Delays During FPGA Placement：机器学习预测延时已有依据，LightGBM 与残差学习本身不作为原创算法。
- Botea, Harabor (2013), Path Planning with Compressed All-Pairs Shortest Paths Data：[作者 PDF](https://pathfinding.ai/pdf/botea-harabor-icaps13.pdf)。全点对路径预处理、下一步动作数据库和压缩属于已有研究。

本项目的创新候选是针对官方 FPGA 图的组合机制：平移共享局部可行路径、以足迹和总行程证书判断跨 Gap 后的适用性、用可行上界限制学习模型，并按源端口建立无损字典。尚未完成系统性新颖性检索，不宣称世界首次；需继续与已有 FPGA 距离表及路径数据库逐项比较。

## 算法

1. 使用官方 Arc/Net，在规则 SRB 区域的有限窗口中为选定源端口运行 Dijkstra。存储端口对与相对位移对应的一条可行路径的代价及足迹。端口集合仅由开发集请求的端口名称确定；生成、压缩不使用 golden。
2. 用四个 4 位数记录路径超出起终点包围盒的左右上下距离，用两个标志记录各轴是否达到覆盖该足迹所需的最小总行程。
3. 查询时平移足迹。超出阵列或与 Block 相交则回退。涉及 Gap 的轴必须满足总行程证书；端点之间的 Gap 加一次延时，端点范围之外但足迹以内的 Gap 加两次延时。不能证明适用时回退。
4. 得到可行路径上界 U 后，将原预测 P 改为 min(P,U)。其他请求保持原模型结果。

### 为什么上界校正成立

如果 D 是实际最短延时，可行路径一定满足 U≥D。当 P>U 时，D≤U<P，因此改为 U 会减小绝对误差以及相对误差；当 P≤U 时不修改。官方正延时评分随相对误差下降而上升，因此在上界正确的条件下，此操作不会降低单条评分。有限窗口路径不保证是实际图上的全局最短路。

### 为什么只用两位就能处理部分 Gap

对每条坐标分界线，净跨越次数由起终点决定。要覆盖包围盒，端点区间中的线至少跨越一次，区间外足迹中的线至少跨越两次。如果某轴总行程等于 |端点差|+2×两侧外伸，那么这些最低次数全部恰好达到，可以按一次或两次计入每条 Gap 的代价；否则拒绝涉及该轴 Gap 的模板。该证书是保守条件，不涵盖所有可复用路径。

## 存储

每个源端口建立 uint32 路径记录字典，表项仅保存 uint16 字典索引。查询为两次读取，保留所有代价、足迹和证书信息。16×16 位移范围共 31,223,808 个表项；原始记录文件 124,896,000 字节，字典文件 71,648,216 字节，最大单源字典 29,817 项。

本轮只确认模板文件占 71.65 MB；完整提交文件尚未打包计量。模板位于忽略目录 out/local-oracle/regular-16-dict.bin，未纳入 Git。研究格式尚未携带架构指纹，使用时必须与本次官方架构匹配；进入部署阶段应增加架构指纹校验。

## 消融：同一固定验证集 150,053 条

| 校正方案 | 高精度 V7 验证分 | 有效覆盖 |
|---|---:|---:|
| 无路径模块 | 94.787671 | 0 |
| 范围12，仅无 Gap 的足迹 | 94.859143 | 402 |
| 范围12，单调轴证书 | 94.920191 | 913 |
| 范围12，总行程证书 | 94.957400 | 1,324 |
| 范围16，总行程证书+无损字典 | **95.041055** | **2,250** |

最后一版修改 V7 的 1,125 条预测；完全匹配从 1,840 条提高至 2,963 条。所有有效覆盖请求中未发现 U<D。该观察支持实现正确性，但有限验证不是所有请求的形式化证明。

快速 V6 路线从 94.020029 提升至 94.310006。C++ 与 Python 两条路线的验证输出均逐行相同，见 V8-cpp-validation.json。只编译并核对本轮算法结果，没有进行提交验收。

## 复现

```sh
python3 scripts/prepare_local_oracle.py
c++ -std=c++17 -O3 src/local_oracle_build.cpp -o build/local_oracle_build
build/local_oracle_build out/local-oracle/ports.txt out/local-oracle/regular-16-v4.bin 16 16 32
out/v4-venv/bin/python scripts/compress_local_oracle.py --input out/local-oracle/regular-16-v4.bin --output out/local-oracle/regular-16-dict.bin
make build/estimate
build/estimate -in out/evaluation/validation.request.csv -out out/evaluation/validation.v8-cpp-v7.csv --algorithm v7-tree --local-oracle out/local-oracle/regular-16-dict.bin
```

## 下一步路线与停止条件

1. 按不同位移、端口族和特殊区域分析残余误差，选择能带来更大覆盖的模板预算分配。比较非对称位移范围，避免只扩大正方形表。
2. 高精度 V7 树模型作为研究老师，其逐树推理目前太慢，不能据此宣称满足十亿请求要求。将它对端口、相位和位移的规律压缩到小型模型，并与带证书上界联合。
3. 扩展跨 Block 模板前必须保存足够路径信息并验证实际连接；不能放宽现有拒绝条件来虚增覆盖。
4. 每个候选保留固定验证集消融、实际存储和适用边界。低收益方案及时停止；多次依据验证集选模型存在选择偏差，最终需要一次独立评估，但当前按用户要求延后。
