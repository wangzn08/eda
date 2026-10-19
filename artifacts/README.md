# 运行快照与共享资产

## V274高精度快照（2026-10-19）

`runtime-v274/`保存实测程序、主模型、冻结源码和构建清单，共约5.68MB；不变架构文件与`runtime-v219/`共用。轻量目录需先组装，完整提交为99,415,300 bytes。

```sh
make runtime-accuracy
build/runtime-v274/estimate -in /absolute/path/request.csv -out /absolute/path/result.csv
python3 scripts/assemble_score_release.py --version 274 --output out/submission/reassembled-v274
```

完整验证99.6344970607；两批新请求十亿CPU外推平均55.8968分钟，峰值RSS1,966,096,384 bytes。高精度版的综合估分仍低于V254，默认`make`继续构建V254。默认及高精度入口都从各自冻结源码重编译，避免后续研究头文件改变已测版本。

源码构建只需C++17、zlib、liblzma和Python3标准库；生成树代码使用临时目录，最终提交不包含重复的完整树表示。预编译程序为M4/macOS ARM64；Linux需重编译，性能尚未实测。[完整结果](../reports/V255-V274-accuracy.md)。


## 2026-10-19：V250 / V253 / V254

`runtime-v253/`、`runtime-v254/`保存实测程序、冻结源码、构建文件与清单。它们共用V219中SHA完全相同的架构资产，只保存新增文件，合计新增约6.68MB。`runtime-v242/`另保留原重复请求阶段的完整冻结源码与程序，`make runtime-v242`可重编译。使用下面的命令组装完整目录；组装会逐项核对程序、模型及源码SHA：

```sh
python3 scripts/assemble_score_release.py --version 254 --output out/submission/reassembled-v254
python3 scripts/assemble_score_release.py --version 253 --output out/submission/reassembled-v253
```

`runtime-v250/`另保留验证99.5290713、约29.06分钟的精度配置，可用`make runtime-v250`组装并编译；其源码重建使用Python3标准库生成临时树代码。

根目录`make`编译V254，输出`build/runtime-v254/estimate`；`make runtime-v253`组装并重编译短专家配置。三个完整提交目录均小于100MB，包含必要模型、许可证和可独立编译源码。提交使用组装后的单个完整目录或对应压缩包。

V254保持验证99.5061105，新请求十亿CPU外推约21.05分钟；V253验证99.5151946，约21.98分钟。均关闭中间算子缓存，测速输入为两批各300万条互不重复的新配对请求。详细指标及适用范围见[本轮结果](../reports/V253-V254-final.md)。Linux性能尚未实测。

## 以下为历史V219快照

`runtime-v219/` 保存最后完成同版完整验证和两轮速度测量的程序及全部必要资产。其七个文件共 94,768,591 bytes。各文件 SHA-256 记录在 [`../reports/V219-joint-goal-profile.json`](../reports/V219-joint-goal-profile.json) 的 `asset_sha256_after` 中，本次复制前已逐项核对。

## 运行

`estimate` 是 Apple M4/macOS ARM64 本机可执行文件；不能直接用于 Linux 比赛环境。全部 `.bin` 文件与许可证应随程序保留在同一目录。示例：

```sh
cd artifacts/runtime-v219
./estimate -in /absolute/path/request.csv -out /absolute/path/result.csv
```

输入为包含 `From,To` 的请求 CSV，输出包含 `From,To,delay`。运行资产不包含请求答案缓存。

## 已完成的测量

| 指标 | 结果 |
| --- | --- |
| 完整验证请求数 | 150,053 |
| 验证分 | 99.51665300760335 |
| 两轮实际速度请求数 | 各 10,000,000 条重复开发请求 |
| 十亿条 CPU 时间外推 | 2345.3416 / 2373.4208 秒 |
| 峰值 RSS | 1,850,851,328 bytes |
| 程序及全部必要资产 | 94,768,591 bytes |

时间外推包含一次初始化与 CSV 读写，只代表本地单线程重复开发请求测量，不代表官方评测机、未见请求或实际十亿条性能。验证分是比赛误差评分，不是预测完全正确比例。99.5 分与 600 秒的联合目标尚未达到。

## 当时源码状态（2026-10-17历史）

仓库当前 `src/` 是继续迭代的研究源码，包含 V220/V222 与此后的未验证改动，并非此二进制的冻结源码快照。尤其最新短程初始化队列、3100 截断与条件下界存储改动尚未重新编译和完成验证。默认 `Makefile` 还保留历史入口，不能据此声称重新构建了该已验证程序。

原始官方数据、Python 环境及大量中间实验产物由 `.gitignore` 排除，其他研究模型、脚本和报告保存在对应目录。整个 Git 仓库的大小与单份比赛提交包的 100 MB 限制是不同的统计范围。
