# 2026 EDA 精英挑战赛 · 赛题一

目标：实现超大规模 FPGA 布局布线的延时估算程序。给定起点和终点 pin，输出最短走线延时。

## 官方资料

- [赛事页面](https://cpipc.acge.org.cn/cw/hp/2c9080158ee9c272018f229208b610a6)
- [赛题指南](https://cpipc.acge.org.cn/sysFile/downFile.do?fileId=e199a7633bda47ebb59331c1831f2faa)
- [论文原文与阅读笔记](papers/README.md)
- [实施计划、验收条件与参考文献](docs/PLAN.md)
- [数据审计与精确基线阶段报告](reports/BASELINE.md)
- [P4 压缩搜索实验](reports/P4-compression.md)
- [P4 位移、Gap/Block 与 C++ 高速候选实验](reports/P4-short-and-cpp.md)
- [P5 已选模型与淘汰理由](reports/P5-selected-model.md)
- [P7 最终本机验收与提交包](reports/P7-final.md)

## 评测要求

- 输入：`delay_estimate_request.csv`，每行包含 `From,To`。
- 输出：`delay_estimate_result.csv`，每行包含 `From,To,delay`。
- 命令行入口：`estimate -in <输入文件> -out <输出文件>`。
- 公开测试集包含 100 万对请求及标准答案；正式评测使用 10 亿对非公开请求。
- 单线程运行；内存不超过 2 GB；完整测试集运行时间不超过 1 小时。运行时间超过 30 分钟时，该项时间分为 0。
- 技术分：准确性 80%、运行时间 15%、结果一致性 5%。评测程序会重复运行 5 次。

以上以官方最新赛题指南和后续 Q&A 为准。

## 项目安排

1. 获取官方 SRB 阵列文件、公开请求及标准答案，放入本地 `data/` 目录。
2. 根据 `SRB_Inst.json`、`SRB_Port.json`、`SRB_Arc.json`、`SRB_Net.json` 和 `SRB_Gap.json` 建立连接与延时模型。
3. 实现可复核的基础算法，并在公开集上统计准确性、耗时和内存。
4. 针对大规模查询优化预处理、查询路径和文件读写。

`data/` 和构建产物不纳入 Git。架构常量已固化在受版本控制的 `src/architecture_data.hpp`，因此直接编译不需要下载原始 JSON；如需依据本地官方 JSON 重新生成，可执行 `make refresh-architecture`。

## 已收到的官方附件

- `data/EDA-PANGO-SRB-Arch-Delay/arch/`：五份架构 JSON，分别有 60,200 个 Inst、496 个 Port、8,192 条 Arc、160 种 Net，以及 19 条 Line Gap 和 7 个 Block Gap。
- `data/EDA-PANGO-SRB-Arch-Delay/data/delay_estimate_ans.csv`：1,000,000 行带答案的公开样本，列为 `From,To,delay`。
- `data/EDA-PANGO-SRB-Arch-Delay/data/delay_estimate_check.csv`：8 行带最短路径的检查样例，列为 `From,To,Min Delay,Path`。
- `data/紫光同创-EDA竞赛/`：两份 DOCX 格式说明，以及 `SRB_LOGIC_PORT.vsd`、`SRB_NET.vsd` 两张连接示意图。
- 仓库根目录的赛题 PDF 是 V0.3 版，日期为 2026-08-31。

压缩包内未见单独的 `delay_estimate_request.csv`；公开答案 CSV 的 `From,To` 两列可用于本地生成请求文件。Block Gap 会改变跨块 Net 的终点，Line Gap 会增加跨越延时，建图时必须按说明文件处理。

## 当前实现与复跑方法

已实现 C++17 高速估算入口和精确参考程序。正式命令默认采用已冻结的端口族×方向查表模型；`--algorithm bidirectional|dijkstra|compressed` 可复核精确最短路。架构和模型参数在构建时内嵌；执行时无需 JSON 或答案文件。

```sh
make -j1
make audit
make check
python3 scripts/prepare_splits.py
python3 scripts/prepare_stress.py
python3 scripts/verify_stress.py
python3 scripts/verify_compression.py
build/estimate -in out/baseline/official8_bidirectional.request.csv -out out/result.csv
```

`make check` 包括规则边界与评分测试、官方8条最短路检查、单向/双向对照、8条开发集样本、同点与重复请求。`out/` 保存生成数据、测量日志和报告；`reports/` 保存阶段快照。大规模百万条精确求解需要明显更长时间，先按计划开展加速实验。

`prepare_stress.py`与`verify_stress.py`负责44组开发集交叉分层样本，当前全部匹配。本机此组耗时约41秒、峰值RSS约0.96GB；这是精确基线的测量，不是比赛运行性能承诺。

实验选项 `--algorithm compressed` 使用Arc/Net严格交替性质，只搜索互联Input状态；44条开发分层样本输出与原图完全一致，本机端到端耗时约19.7秒、峰值RSS约0.34GB。原图双向Dijkstra仍可用 `--algorithm bidirectional` 运行独立对照。

实验选项 `--algorithm approximate` 使用开发集离线拟合并内嵌的位移表、端口偏置和 Gap/Block 校正，执行时不读取 golden。在15万独立验证请求上得分86.89，本机70万请求进程CPU约0.244秒、峰值RSS约18.4MB。正式隐藏集准确率和十亿请求全流程尚未确认；当前默认入口仍为精确参考算法。

当前正式入口为 `--algorithm port`：在上述特征上增加粗网格位置对、端口族×方向校正，验证评分90.89、最终留出评分90.86。不传 `--algorithm` 时即运行这一模型。本机五次十亿请求完整运行均约192–198秒、峰值RSS约3.5MB且输出完全一致；[独立源码包](out/submission/fpga-delay-estimator-source.tar.gz)可脱离数据目录编译。十亿请求的大型临时 CSV 已在验收后清理，脚本可以重新生成。官方评测环境和上传格式以赛事系统为准。

开发/验证/最终留出按请求对哈希固定划分为 700,705 / 150,053 / 149,242 条。请求和golden分文件保存，最终留出尚未用于算法评估。输入全量审计发现1条golden=0；评分工具单独报告零延时样本，不擅自补充官方未定义的除零规则。
