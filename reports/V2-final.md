# 赛题一：V2 本机验收

## 模型与精度

默认 C++17 程序采用端口族与方向基线，再加入源列、目标列和精确横向位移残差查表。参数仅由开发集拟合，验证集用于模型选择；最终留出集在方案冻结后评估，没有用于调参。模型选择依据与文献背景见 [V2 优化记录](V2-optimization.md)。

| 模型 | 固定验证集评分 | 最终留出集评分 |
|---|---:|---:|
| V1 | 90.8892 | 90.8589 |
| V2 | **92.5315** | **92.4866** |

留出集共149242条请求，V2 相对误差 P50/P95/P99 为 **1.077% / 6.569% / 15.520%**；输出 SHA-256 为 `ea1b657e98c0b7bd82247469fcf46c8355f446abbcd0fe36822858e24d9f582d`。详见 [机器可读留出报告](V2-holdout.json)。公开数据划分不能替代正式隐藏数据。官方 V0.3 对零延时分母未规定评分方式；留出集中没有零延时请求。

## 十亿条请求的五轮端到端验证

输入为固定开发集请求重复生成的十亿行 CSV，每轮均完整读取、预测、写出十亿行。五轮输出字节数均为40332662632，SHA-256 均为 `fd3f9702747db1f9678bbd611b75e97cfb288d1609a63f88ef1410622bf262f7`。输入和输出数据文件可由脚本重建，记录见 [机器可读基准](V2-benchmark.json)。

| 运行 | 墙钟秒 | 进程 CPU 秒 | 峰值 RSS MB |
|---:|---:|---:|---:|
| 1 | 201.85 | 200.033 | 3.817 |
| 2 | 202.09 | 199.918 | 3.817 |
| 3 | 204.70 | 202.498 | 3.817 |
| 4 | 204.77 | 202.639 | 3.817 |
| 5 | 196.49 | 195.370 | 3.834 |

平均进程 CPU 为200.0916秒。按本机时间、留出集精度和五轮一致性估算的综合分约 **92.32**；这是本机模拟值，不是官方评测分。五轮均低于1小时与2GB限制。V1 同机五轮约192–198秒，V2 的精度提升以小幅运行时间增加为代价。评测机的 CPU、编译器、磁盘与隐藏数据分布可能不同。

## 交付检查

- 默认入口与显式 `--algorithm v2` 的验证集输出逐字节一致；`make check` 已通过。
- 独立源码包 [fpga-delay-estimator-v2-source.tar.gz](../out/submission/fpga-delay-estimator-v2-source.tar.gz) 为351256字节，SHA-256 `cfd86854c183352f1af46e97b2a3be4b59c34f62cd5815c2a819e2d28364e878`。包内含 C++17 源文件、内嵌模型参数和编译说明。
- 在无原始数据目录的独立解压目录编译源码包后，150053条验证请求输出 SHA-256 与仓库程序相同，均为 `c9535dffce359c2acc5a76d4297ed3cffd431e69fca88af4f4a9cbcef9c44f28`。
- V1 的 Git 历史和原独立源码包保留。正式上传格式与目标环境须以赛事系统要求为准；V2 尚未在官方评测机运行。

复跑命令：`make -j1 && make check`；`python3 scripts/prepare_repeated_stress.py --rows 1000000000 --out out/evaluation/stress1b.request.csv`；`python3 scripts/verify_repeated_benchmark.py --input out/evaluation/stress1b.request.csv --output out/evaluation/stress1b.v2.csv --rows 1000000000 --runs 5 --report out/evaluation/benchmark1b-v2.json`；`python3 scripts/package_submission.py`。大型临时 CSV 在验收后清理。
