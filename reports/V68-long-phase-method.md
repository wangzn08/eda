# V68：长线源端口的无损周期下界投影

原PHASELB4记录全部160个网线到达端口。本宏图只查询32个长线到达端口，因此保留这32个源端口、全部496个目标、4个方向势函数与完整120个相位，并仅保存被引用的模式。新增PHASELB5格式支持源端口子集，原格式继续读取。

数据完全来自既有架构模式数据库，不使用请求答案。重新编码后资产10117278字节，原资产47019458字节；解码6339000个模式值，全部编码往返一致。比较32×496×120×4=7618560个下界查询（包含四个坐标方向），零差异。1001条独立宏搜索试点输出与完整PDB逐字节相同。

这是Culberson/Schaeffer模式数据库方向的用途裁剪，并非新的路径估算算法。子集资产不能用于全160端口搜索；未覆盖端口仍显式报错，避免误用。该宏图当前评分仍约94.64，不能据此宣称99.9目标达成。

复现：编译src/project_long_phase_bounds.cpp，输入out/architecture-benchmark/phase-bounds.dictionary.bin，输出PHASELB5资产；编译src/compare_long_phase_bounds.cpp，与models/phase-bounds-safe.bin比较。src/compress_phase_bounds.cpp继续保留原始格式导出。缩减资产与当前宏可执行程序、long-tail.bin合计大小见V68-long-phase-assets.json，不是最终提交验收。
