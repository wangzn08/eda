# 赛题一：本机最终验收

## 固定版本

- 默认命令：`estimate -in requests.csv -out results.csv`，运行 `port` 架构感知分层查表模型。
- 编译：C++17，`-O3`；本机为 Apple M4、macOS arm64、Apple clang 21.0.0。
- 所有架构与模型参数已内嵌；受版本控制的 `src/architecture_data.hpp` 让仓库本身也能脱离原始 JSON 编译。运行时不读取答案、训练 CSV 或 JSON。精确参考算法仍可通过 `--algorithm bidirectional|dijkstra|compressed` 单独使用。
- `make check`：6个几何/评分单元检查通过；官方8条路径和开发集零延时/重复请求的精确参考检查通过。默认快速入口与显式 `--algorithm port` 的15万验证输出 SHA-256一致。

## 精度与一致性

| 数据 | 请求数 | 官方正延时公式评分 | 相对误差 P50 | P95 | P99 |
|---|---:|---:|---:|---:|---:|
| 固定验证集 | 150053 | 90.8892 | 1.388% | 7.843% | 17.435% |
| 最终留出集（方案冻结后首次评估） | 149242 | **90.8589** | **1.382%** | **7.900%** | **17.235%** |

留出集输出 SHA-256：`569cc85094ecfcfac0d9b8b8c42792b3942f62dd998a763c6ebc657aa656c426`。公开百万答案里唯一的零延时同点请求在开发集；默认程序输出0。官方 V0.3 未规定零分母的评分方式，因此上表只按正延时公式计算。详见 [机器可读留出报告](P7-holdout.json)。公开集哈希划分不能代替正式隐藏数据；没有根据最终留出结果回调参数。

## 十亿条端到端压力测试

输入由开发集无标签请求重复生成，恰好十亿行，输入36,394,618,757字节。五次均使用同一可执行文件和同一输入，完整写出40,332,856,745字节，每次程序均报告十亿行；五份输出 SHA-256 全相同：`28980113bff98673de78f1199e5edab3920536a27ce9b41a3138822d03fcf8b7`。

| 运行 | 墙钟秒 | 进程 CPU 秒 | 峰值 RSS MB |
|---:|---:|---:|---:|
| 1 | 193.78 | 192.80 | 3.46 |
| 2 | 197.57 | 192.14 | 3.46 |
| 3 | 192.29 | 191.34 | 3.46 |
| 4 | 193.11 | 191.61 | 3.44 |
| 5 | 192.48 | 191.45 | 3.47 |

五次本机运行均低于1小时、2GB，且进程CPU低于30分钟的时间分界。本机是 macOS Apple M4，不能代替赛题评测系统的操作系统、CPU、编译器和 I/O 环境。十亿输入为开发请求重复，不代表隐藏请求的精度或端点分布。完整资源与哈希记录见 [机器可读基准](P7-benchmark.json)。

## 可移植交付

已生成独立 C++17 源码包：[fpga-delay-estimator-source.tar.gz](../out/submission/fpga-delay-estimator-source.tar.gz)，218,331字节，SHA-256 `602b5e045035651d97fe39872c265a88514420d936201b275e8f4b821416d7a9`。包内有 `estimate.cpp`、架构与模型头文件、编译与运行说明；在不读取项目 `data/` 目录的独立解压目录编译，验证输出与仓库程序逐字节一致。包元数据已归一化，重复打包的哈希相同。

2026赛事官网当前显示作品提交截至 **2026-11-07**：[官方赛事页](https://cpipc.acge.org.cn/cw/hp/2c9080158ee9c272018f229208b610a6)。实际上传格式、评测镜像及目标机器仍须以赛事评测系统的赛题页面最新说明为准。此包是本机验证过的可移植源码交付，尚未在官方评测系统运行或上传。

复跑：`make -j1 && make check`；`python3 scripts/prepare_repeated_stress.py --rows 1000000000 --out out/evaluation/stress1b.request.csv`；`python3 scripts/verify_repeated_benchmark.py --input out/evaluation/stress1b.request.csv --output out/evaluation/stress1b.final.csv --rows 1000000000 --runs 5 --report out/evaluation/benchmark1b.json`；`python3 scripts/package_submission.py`。十亿请求临时 CSV 已于验收后清理，保留机器可读报告、输入/输出哈希及生成脚本。
