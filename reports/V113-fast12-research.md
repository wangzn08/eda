# V113：不同架构争取12分钟，迭代中

## 目标与基线

用户授权持续探索不同架构以争取更高排名。工程阶段目标：完整validation赛题分至少99；单线程十亿CPU含一次初始化、CSV读写的本机外推不超过720秒；100MB运行文件、2GB内存。保留V112标准配置99.0256649、14.7500/14.8184分钟。第一名尚无官方排行榜或隐藏评测依据，不能保证。

不读取holdout，不运行完整十亿，不使用请求结果缓存；development重复请求用于小规模真实吞吐，validation只做比较。

## 路线

1. **水平距离融合**：将有限模板基值与水平瞬态的首段基值、后续增量合成4字节记录，按目标核心端口、相位、源核心端口排列。查询减少独立数组访问，数值公式相同。原型额外分配145MB导致RSS2,107,375,616 bytes，超出2GB，淘汰其分配方式；改为移用原水平数组、先局部变换再原地循环置换，临时9MB位图，完整validation与V112逐字节相同，RSS1,961,951,232 bytes，初始化70.2847秒。
2. **批量流水线**：收集16/64条请求，分两阶段预取候选索引、距离记录，再按原顺序计算和输出。每条请求都重新计算，不复用答案。批次使用固定小数组保存文本，防止CSV读取缓冲区换页导致字符串失效。额外补齐核心终点的直接记录预取。
3. **紧凑索引加自适应路线**：近距离接入索引最多24种，用5bit代替8bit，保留所有候选选择值，预计节省约72MB。利用空间为源8候选保存其中最佳4候选的子集索引；远阶段只算4，近阶段保留8，比较距离门槛108与36。源子集由架构模板编译，标签不参与排序。自适应属于有损近似，需要完整validation确认。

## 参考文献与贡献边界

[Kocberber等2015，AMAC](https://www.vldb.org/pvldb/vol9/p252-kocberber.pdf)：读取第2/3节。其独立请求状态与内存延迟隐藏提供依据。本轮静态批量预取属于先行原型，未复现完整AMAC异步状态调度，也不能借用原文数据库的加速倍数。配合此前Hook2017 min-plus候选分解及Botea/Harabor2013预处理思路。

原地数据融合、近距离索引压缩和周期候选的距离分段组合为本项目探索方向；预取、位图置换与位压缩均是已知技术，不声称学术首创。

## 实验

`scripts/experiment_fast12_architectures.py`逐个串行跑完整validation和真实开发百万请求，先筛选架构，再用千万请求两轮独立复测。初筛百万外推不能直接当作最终成绩。完整日志、CSV位于out/v113，指标汇总V113-fast12-architecture-pilot.json。

## V115: algebraic coefficient compaction

The wide diagonal cell used to store 18 bytes. Its near vertical slope is unused; horizontal slope is exactly max(0, horizontal_delta); far vertical slope is exactly max(0, base[3]-base[2]). Keeping only the four bases and two signed deltas makes it 12 bytes. The short vertical record likewise becomes 8 instead of 10 bytes by deriving its slope from the last two bases. This removes 146,227,200 bytes of redundant coefficients without fitting labels or changing the recurrence. Full validation parity and observed peak RSS are required before adoption.

V114 full logical-target horizontal records kept validation byte-identical but reached 2,152,628,224 bytes RSS, so they are rejected in their uncompressed form. Shared corridor legs also kept outputs identical; their million-request pilot estimate was 731.25 seconds, so this isolated change is not yet enough for the 720-second stage.

## Preliminary compact-layout result

V115 compact32 preserves all 150,053 validation predictions and score 99.0256649430261. Actual 1m pilot: initialization 71.9973 CPU seconds, query 0.6158, billion extrapolation 687.7973 seconds. Peak RSS 1,624,588,288 bytes. This is screening evidence only; frozen standard-entry validation and two serial 10m measurements are pending.

The compaction differs from choosing fewer routes: it removes algebraic redundancy and preserves the existing candidate search. Batch prefetch borrows the memory-latency-hiding motivation of Kocberber et al., *Asynchronous Memory Access Chaining*, PVLDB 9(4), 2015, https://www.vldb.org/pvldb/vol9/p252-kocberber.pdf . This implementation uses staged fixed batches, not the paper's full independent-state AMAC engine. Corridor leg sharing exploits the repeated subexpression in a min-plus route evaluation; in isolation it did not win the pilot. Validation parity is empirical evidence on the visible validation distribution, not an official hidden-data guarantee or proof that original candidate pruning is exact.
