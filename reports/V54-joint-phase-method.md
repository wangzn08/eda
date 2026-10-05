# V54：联合周期相位与评分损失（进行中）

## 动机与结构

V53的较快距离组合已达到97.1350，但离99.9仍远。原路径专家的源端相位是`S(port,rx,ry,r)=embedding(port,r)+Ax(port,rx,r)+Ay(port,ry,r)`，横纵相位可分离，难以直接表达端口特定的横纵余数交互。

本轮改为`S(port,q,r)=embedding(port,r)+sum_k factor(port,k)*joint(q,k,r)`，其中`q=12*rx+ry`，120种联合余数，rank8；目标端同样处理。再加小型ReLU几何专家，硬min取候选，PDB下界加非负差值。潜在专家不是实际路径证书。

比较32宽/128专家、32宽/256专家、64宽/256专家。选择较小几何网络抵消更多专家的运算。训练直接最小化development上的连续评分损失`mean(tanh(4*abs(pred-golden)/golden))`，不含取整。前96轮软min逐步退火，后32轮硬min。负差值正向截断、反向使用直通梯度以防失活，属于训练近似，不代表严格梯度优化整数评分。

固定validation每8轮查看，同时记录直接模型及距离150混合分。未读取holdout。模型及门限反复选择存在乐观偏差。首个配置早期表现不足以证明有效，全部训练和实际C++速度结束前不切换V53。

## C++实现与当前证据

TINYROU3资产保存源/目标端口嵌入、rank8端口因素、120相位矩阵。查询做两次rank8到专家通道的乘积；原分离因素格式需四次。新增32几何宽和256/512专家维度限制，连续输出通道SIMD布局保留。

- 已编译两种C++入口，原V53完整150053条输出与扩展内核逐字节一致。
- 联合模型epoch40试导出因子资产1553676 bytes；完整validation与未量化Python有12条相差1ps，最大差1ps。
- 该试导出只证明格式及推理对照，不证明最终精度或吞吐。
- 主训练运行中；串行CPU流水线等待训练完成，按配置选检查点，完整验证，再测1000万关闭缓存，含初始化估算十亿。
- 模型固定运行文件仍需最终导出后确认，不能将模型参数数量作为实际提交大小。

## 参考及创新边界

- [Hook 2017，min-plus低秩网络结构](https://arxiv.org/abs/1708.06552)：路径专家表达参考。
- [Kolda与Bader 2009，Tensor Decompositions and Applications](https://epubs.siam.org/doi/abs/10.1137/07070111X?journalCode=siread)：多维因素分解与展开的参考。本轮将横纵余数合成联合索引，用矩阵展开的rank8因素，不声称完整实现CP或Tucker算法。
- PDB及CPU向量化依据延续V51报告。

联合相位、min-plus、直通估计和评分损失本身均非新发明。研究候选是本题周期路由结构下的联合相位表达与微秒预算实现。是否有效由完整实验决定，不以架构更复杂作为成功证据。

## 复现

训练：`out/research-env/bin/python -u scripts/experiment_v54_joint_routes.py`。

训练完成后CPU流水线：`scripts/run_v54_cpu_pipeline.py --wait-pid <training pid>`。导出：`scripts/export_tiny_routes.py checkpoint.pt model.bin --phase-format factor`。
