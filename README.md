# 2026 EDA 精英挑战赛 · 赛题一

目标：实现超大规模 FPGA 布局布线的延时估算程序。给定起点和终点 pin，输出最短走线延时。

## 当前：全新请求十亿外推不超过 10 分钟

| 配置 | 完整验证分 | 十亿新请求 CPU 外推，含初始化 | 两批范围 | 完整提交 |
| --- | ---: | ---: | ---: | ---: |
| **V306，默认，综合与时间余量优先** | **99.1137582** | **8.1433分钟** | 8.13–8.16分钟 | 99.95MB |
| **V309，预算内精度优先** | **99.1170274** | **9.4367分钟** | 9.20–9.67分钟 | 99.86MB |
| V254，旧高精度选项 | 99.5061105 | 21.0482分钟 | 21.03–21.06分钟 | 96.65MB |
| V274，旧最高精度选项 | 99.6344971 | 55.8968分钟 | 55.87–55.92分钟 | 99.42MB |

两个新版本均由同一冻结程序完成完整150053条验证和两批各300万条互不重复的新配对请求测量；不运行完整十亿条，不使用最终预测缓存或中间算子缓存。峰值RSS约1.712GB。每批分别满足600秒，而非仅平均通过；完整文件均小于100,000,000 bytes；独立重编译得到的机器码乃至整个程序SHA均与实测文件相同。

**精度尚未保住原V254水平**：十分钟内已达到99.11分，但尚未同时达到99.5分与新请求600秒。旧高精度版本保留。按此前“综合技术分尽量高”的选择，默认用时间余量更大的V306；本机代入公式并暂设一致性100，其综合估分约95.2194，V309约94.5753，均非官方成绩。

```sh
make
build/runtime-v306/estimate -in /absolute/path/request.csv -out /absolute/path/result.csv
make runtime-budget-accuracy
build/runtime-v309/estimate -in /absolute/path/request.csv -out /absolute/path/result.csv
```

- [本轮架构、容量比较与失败记录](reports/V275-V310-budget-progress.md)
- [V306同版完整测量](reports/V306-budget-profile.json) · [完整提交与重建](reports/V306-budget-submission.json)
- [V309同版完整测量](reports/V309-budget-profile.json) · [完整提交与重建](reports/V309-budget-submission.json)
- [精度优先筛选](reports/budget-accuracy-selection.json) · [综合估分优先筛选](reports/budget-technical-selection.json)
- 完整包：`out/submission/final-v306/`、`final-v309/`；对应归档位于同一父目录。从Git快照组装见[资产说明](artifacts/README.md)。`make runtime-v254`与`make runtime-accuracy`保留旧高精度配置。

时间口径为Apple M4/macOS单线程CPU、小批量全新配对请求外推，包含一次初始化和CSV；不保证另一台机器或其他隐藏输入分布的速度，验证分也不是完全正确的比例。

下方均为历史记录，当前选择以本节为准。

## 2026-10-19：V274精度专项

| 配置 | 完整验证分 | 十亿新请求CPU外推 | 完整提交 |
| --- | ---: | ---: | ---: |
| V254 综合优先，默认 | 99.5061105 | 21.0482分钟 | 96.65MB |
| V274 精度优先，可选 | 99.6344971 | 55.8968分钟 | 99.42MB |

V274扣分较V254减少25.99%，P99绝对误差55→41ps；同一冻结程序完成150053条验证和两批各300万条独立新请求测速。峰值RSS1,966,096,384 bytes，完整提交99,415,300 bytes，独立重编译的文件支持Mach-O节全部一致。

**精度提高，但综合估分尚未超过V254**：本机代入公式、暂设一致性100，V274约84.7076，V254约89.0808。因此`make`继续从冻结源码构建V254；`make runtime-accuracy`构建高精度V274，输出`build/runtime-v274/estimate`。两版都保留。上述时间是本机单线程CPU外推，包含一次初始化和CSV，不是十亿实跑或官方成绩。

- [新架构、全部对照、文献与取舍](reports/V255-V274-accuracy.md)
- [V274同版完整测量](reports/V274-native-score-profile.json) · [交付与源码重建](reports/V274-submission-audit.json) · [逐行误差变化](reports/V274-error-summary.json)
- 完整包：`out/submission/final-v274/`；压缩包：`out/submission/fpga-delay-v274.tar.gz`。Git轻量快照与共享资产组装见[说明](artifacts/README.md)。

下方保留上一轮和历史记录，当前选择以本节为准。

## 2026-10-19：全新请求优化，保留三种配置

| 配置 | 完整验证分 | 十亿新请求CPU外推，含初始化 | 完整提交目录 |
| --- | ---: | ---: | ---: |
| V254 综合优先（默认） | 99.5061105 | 21.0482分钟 | 96.65MB |
| V253 短专家，验证分更高 | 99.5151946 | 21.9761分钟 | 97.75MB |
| V250 较高精度可选 | 99.5290713 | 29.0628分钟 | 98.09MB |
| V242 新请求基准 | 99.5061105 | 25.1441分钟 | 96.62MB |

三版都对两批各300万条互不重复的新配对请求完成标准测量，完整验证为150053条；中间算子缓存关闭，最终预测缓存关闭。V254完整验证及600万条新请求的输出与V242逐字节一致。峰值RSS分别为1,962,016,768 / 1,963,573,248 bytes，均低于2,000,000,000 bytes。

按现有公式、以验证分和本机CPU外推代入并暂设一致性100分，V254技术分估算由87.0328提高至89.0808。这不是官方隐藏集成绩或五轮正式验收；每条时间是批量平均CPU，速度不保证适用于其他分布和机器。V254约1.130微秒/条，V253约1.183微秒/条。

- [本轮结果、取舍和复现](reports/V253-V254-final.md)
- [多架构实验与失败记录](reports/V243-V251-research-progress.md)
- [V254同版测量](reports/V254-native-score-profile.json) · [交付审计](reports/V254-submission-audit.json)
- [V253同版测量](reports/V253-native-score-profile.json) · [交付审计](reports/V253-submission-audit.json)
- `make`输出`build/runtime-v254/estimate`；`make runtime-v253`输出短专家版。原重复请求约9分钟的V242冻结版本保留，可用`make runtime-v242`重编译。
- 提交使用`out/submission/final-v254/`或`final-v253/`单个完整目录；对应压缩包已在`out/submission/`生成。V250可用`make runtime-v250`重编译；源码快照与模型保存在`artifacts/`，共用不变的架构资产；重新组装方式见[快照说明](artifacts/README.md)。

```sh
make
build/runtime-v254/estimate -in /absolute/path/request.csv -out /absolute/path/result.csv
make runtime-v253
```

下方保留较早阶段原始记录，当前选择以本节为准。

## V242：重复请求阶段的历史联合目标（2026-10-18）

同一标准版本完整150053条验证分 **99.5061105**；两轮实际一千万条请求，十亿CPU外推 **536.2104 / 534.0712秒**，均含初始化与CSV；峰值RSS **1,928,036,352 bytes**。完整程序、资产、许可证、可独立编译的20份源码与构建说明约 **96.62MB**。99.5分/600秒/100MB/2GB的约定本机联合目标已达到，停止本轮优化。

**时间口径：** 输入为700,705个不同开发请求对重复至一千万条。新版本复用中间架构算子，命中率约92.35%；不缓存最终预测。这个速度不能直接用于未见且缺少算子复用的请求，也不是官方Linux评测结果。验证分是比赛误差评分，不是预测完全相等比例。

**2026-10-19 新请求补测：** 同一 V242 对600万条新配对且互不重复的请求，分两轮测得平均每条CPU约 **1.42微秒**，中间算子缓存命中率约 **0.10%**。十亿条含一次初始化外推约 **25.1分钟**（两轮24.9–25.4分钟）。这是本机合成请求测量，不是官方隐藏集速度或新请求准确率；详见[新请求测速报告](reports/V242-novel-requests.md)。

- [完整结果、算法、限制与复现](reports/V242-final.md)
- [标准运行原始指标](reports/V242-joint-goal-profile.json) · [逐项完成审计](reports/V242-joint-goal-audit.json)
- [V223–V237及后续迭代过程](reports/V223-V237-runtime-architecture-progress.md)
- 本地完整目录：`out/submission/final-v242/`；压缩包：`out/submission/fpga-delay-v242.tar.gz`。
- 当前默认构建入口改为V242：`make`（也可`make -f Makefile.runtime`），输出`build/runtime-v242/estimate`，必要模型随程序复制。程序与模型可用以下命令运行：

```sh
build/runtime-v242/estimate -in /absolute/path/request.csv -out /absolute/path/result.csv
```

下方2026-10-17上传记录和更早版本说明保留为历史；V219运行快照仍可独立使用。

## 历史上传快照（2026-10-17）

这是持续研究中的代码仓库。最后完成同版完整验证和两轮测速的版本为 V219：验证分 **99.516653**，本机单线程十亿条请求 CPU 时间外推 **2345.34–2373.42 秒**，峰值 RSS **1,850,851,328 bytes**，程序及必要资产合计 **94,768,591 bytes**。时间由实际一千万条重复开发请求测量后外推，包含一次初始化与 CSV 读写，不是官方机器或真实十亿条测量；验证分不是预测完全相等的百分比。同版 99.5 分与 600 秒的联合目标尚未达到。

- [V219 已验证程序、资产与运行说明](artifacts/README.md)
- [V219 完整测量记录及资产 SHA-256](reports/V219-joint-goal-profile.json)
- 当前 `src/` 包含 V219 之后的实验改动，其中短程初始化队列与条件下界存储等最新改动尚未重新编译和完成验证；不能将当前源码直接标为 V219 的已验证源码。
- 下方较早阶段的版本、默认构建入口与验收结论均为历史记录，当前状态以本节和对应版本报告为准。

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
- [V2 列感知准确率优化](reports/V2-optimization.md)
- [V2 最终本机验收与提交包](reports/V2-final.md)
- [V3 路径结构研究与创新点](reports/V3-route-research.md)
- [V3 最终本机验收与提交包](reports/V3-final.md)
- [V4 准确率提升与本机验收](reports/V4-accuracy.md)
- [V5 结构化路径模型研究](reports/V5-structured-research.md)

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

已实现 C++17 高速估算入口和精确参考程序。本研究分支的仓库入口默认采用 V6；独立 V14 验收包默认采用 V14（见下方验收报告）。`--algorithm bidirectional|dijkstra|compressed` 可复核精确最短路。架构和模型参数在构建时内嵌；执行时无需 JSON 或答案文件。

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

早期实验选项 `--algorithm approximate` 使用开发集离线拟合并内嵌的位移表、端口偏置和 Gap/Block 校正，执行时不读取 golden。在15万独立验证请求上得分86.89，本机70万请求进程CPU约0.244秒、峰值RSS约18.4MB；该方案已被后续版本取代。

V1 `port` 模型在验证/留出集的评分为90.89/90.86，本机五次十亿请求约192–198秒且输出一致；[V1独立源码包](out/submission/fpga-delay-estimator-source.tar.gz)继续保留。V2 增加源列、目标列与精确横向位移校正，验证/留出集评分为92.53/92.49，本机五次十亿请求约196–205秒。V3 进一步利用官方架构的 Block 绕行与端点固定 Net 方向，验证/留出集评分为92.84/92.82，五次十亿请求约208–212秒。V4 加入纵向与横向的端口条件修正，验证/留出集评分为93.41/93.40；历史 V4 稳定版不传 `--algorithm` 时运行 V4；本研究分支当前默认 V6。[V4 报告](reports/V4-accuracy.md)记录方法与验收；V1/V2/V3 源码包仍保留。十亿请求的大型临时 CSV 可由脚本重新生成。官方评测环境和上传格式以赛事系统为准。

研究分支另有 `--algorithm v5-geometry` 与 `--algorithm v5-geometry-fused`。前者留出分为93.5040，后者验证分为93.5160；额外运行成本使其暂不替换 V4 默认版，详见 [V5 研究](reports/V5-structured-research.md)。

开发/验证/最终留出按请求对哈希固定划分为 700,705 / 150,053 / 149,242 条。请求和 golden 分文件保存，每版最终留出只在候选冻结后评估。输入全量审计发现1条 golden=0；评分工具单独报告零延时样本，不擅自补充官方未定义的除零规则。

## V14 完整流程验收（2026-10-04）

候选已冻结，独立包解压后从源码重编译，使用标准 `-in/-out` 命令复跑。验证分97.2235，最终留出分97.2099。压缩包49.36MB。完整资源、重复性能与新请求速度限制见 [V14 验收报告](reports/V14-final.md)。

## 精度优先研究（2026-10-05）

当前C++候选V19验证分为 **97.408215**，通过补全长导线跳数枚举并重新训练上界特征得到。需显式指定 `--algorithm v19-tree` 及两份路径资源；仓库默认仍为V6。留出集、本轮提交包和十亿请求性能未重新验收。实验结果、参考文献及复现命令见 [V16–V19研究报告](reports/V16-V19-accuracy-research.md)。

## 最新精度研究：V20–V35

跨类别模型、残差神经网络、路线 min-plus 和周期相位张量进行了比较。C++预测组合验证分97.952110；增加输入距离及模型分歧触发的精确A*后，首次完整验证98.387821。后者是混合求解分数，尚不满足独特请求的大规模吞吐要求，也没有达到99.9。模型权重已保存在 `models/`；不替换默认入口。详见 [架构研究、文献和复现命令](reports/V20-V35-architecture-research.md) 和 [验证数据](reports/V35-adaptive-validation.json)。

## V40：验证分99.9阶段目标已达到

完整固定验证150053条得分 **99.9963756**；V40使用官方架构生成的周期模式下界与误差控制搜索，不依赖神经模型。约95.45%的延时完全一致，所有误差区间核对通过。CPU447.952秒、RSS约506MiB；大规模独特请求吞吐仍有明显差距，尚未完成正式验收。独立运行目录为 `out/phase-precision-v40/`，必需程序与资产合计约59.85MB。

[研究、证明条件、文献及运行命令](reports/V36-V40-precision-research.md) · [完整验证记录](reports/V40-full-certified-validation.json)
