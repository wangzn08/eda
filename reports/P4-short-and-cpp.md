# P4 第四项实验：短距离策略与 C++ 近似入口

## 短距离策略判断

定义端点曼哈顿距离≤20。开发集有8601条、验证集1881条。距离表原型在此组为49.25分；另用短距离开发样本拟合1/1、2/2、2/4、4/4四种细桶，最佳仅50.81分，不能解决误差。现有 Gap/Block 校正模型在同一组为50.76分。短距离专用表因此暂不采用。

对30条短距离验证请求使用压缩图精确求解，本机单条耗时中位数约0.68毫秒、P95约8.43毫秒、最大约23.05毫秒（不含每次程序启动成本）。在十亿查询中即使这类请求只占约1.25%，常规精确回退也明显不适合时间预算。需另研究局部结构预计算；也可先接受此组误差，把时间用于更高占比的请求。

## C++ 固化与结果

`scripts/export_lookup.py` 仅从固定开发集训练，把位移表、起终端口偏置和 Gap/Block 校正输出为编译期常量 `src/lookup_model.hpp`。程序运行时不读取答案文件。`--algorithm approximate` 使用请求端点和已内嵌的架构数据做常数规模查表；原精确选项仍保留供对照。

在完整150053条验证请求上，C++ 输出的官方正延时评分为 **86.89164754303984**，P50/P95/P99相对误差为 **2.069% / 11.679% / 23.692%**，与 Python 原型结果一致；有722条整数延时完全命中。验证集无零延时行。此结果属于公开答案哈希划分的验证集，不代表正式隐藏集。

本机 Apple Silicon、Apple clang 21、`-O3` 下，70万条开发请求端到端进程 CPU 时间约 **0.244秒**、墙钟约 **0.24秒**、峰值 RSS 约 **18.4MB**。15万条验证请求 CPU 时间约0.085秒、峰值RSS约18.4MB；小批墙钟受到程序启动和工具测量波动影响。按70万条线性外推十亿条约348秒 CPU，只是吞吐初估；尚未生成十亿行文件，不能据此宣称官方硬件、磁盘和五次运行均合规。

命令：

```sh
python3 scripts/experiment_short.py
python3 scripts/export_lookup.py
make -j1
build/estimate -in out/evaluation/validation.request.csv -out out/evaluation/validation.approximate.csv --algorithm approximate
python3 scripts/evaluate.py --golden out/evaluation/validation.golden.csv --result out/evaluation/validation.approximate.csv
```

下一步：考察短距离局部预计算的空间需求，并对近似模型做距离/端口/特殊区域分层误差分析。方案冻结后才使用最终留出集。
