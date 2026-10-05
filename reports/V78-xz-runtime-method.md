# V78：可移植XZ解码接入

采用Tukaani项目XZ Embedded的官方用户态嵌入方式：复制8个解码源码/头文件及COPYING、AUTHORS，固定上游提交，原文件保持不变。来源与版本见src/vendor/xz/PROVENANCE.md。官方说明：https://github.com/tukaani-project/xz-embedded 。许可证0BSD；C99解码对象链接到C++17估算器，不调用外部解压程序，不依赖系统liblzma或Apple Compression框架。zlib依赖仍用于原核心/垂直残差格式。

COREXZ01解码要求CRC32校验成功、输入全部消耗、输出恰好214476800字节；沿用架构哈希、端口映射及二维逆变换数值检查。原COREZL01格式继续支持。

完整150053条验证输出与V77最大增长范围方案逐字节相同，分数97.971443。CPU2.92787秒，其中初始化2.57941秒；不能把这个总时间与V77查询时间混用。提交资产与二进制合计见V78-xz-runtime-parity.json，低于100MB，仅代表研究运行文件，不包含最终打包或Linux环境验收。

下一步以此新架构重新拟合残差，并评估完整CSV吞吐，不将本轮文件小于100MB当作达成精度/速度目标。
