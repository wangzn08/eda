# 2026 EDA 精英挑战赛 · 赛题一

目标：实现超大规模 FPGA 布局布线的延时估算程序。给定起点和终点 pin，输出最短走线延时。

## 官方资料

- [赛事页面](https://cpipc.acge.org.cn/cw/hp/2c9080158ee9c272018f229208b610a6)
- [赛题指南](https://cpipc.acge.org.cn/sysFile/downFile.do?fileId=e199a7633bda47ebb59331c1831f2faa)

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

`data/` 和构建产物不纳入 Git，避免提交大型赛题数据或本地生成文件。
