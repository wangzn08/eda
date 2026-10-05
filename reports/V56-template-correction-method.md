# V56：压缩架构模板的有符号修正（排队）

V55固定周期模板96.35分，周期包络更差。现在检查有限模板误差是否能用小型模型校正。原V50是从PDB下界增加非负差值；这里模板不是下界，所以训练有符号差值`(golden-template)/100`，推理`round(max(0, template+100*correction))`。

输入仍是71个架构、端点、端口图、长线接入及周期特征，但其中原下界特征替换为模板预测。运行时Line Gap特征直接从架构计算，不读取47MB PDB资产。训练只用development，固定validation比较64/128/256/512/1024棵depth10树；使用加权MAE，权重1/golden。理论最高配置接近100MB，实际三份运行文件超过100000000 bytes的配置直接淘汰，不测速。

训练及串行测速排队等待V54完整CPU报告完成，避免互相干扰。每个可用配置完成全validation、C++/Python逐条一致核对，再测1000万关闭缓存并估算十亿，初始化单独计入。不使用holdout，不宣称正式验收。还无V56结果。

## 实现与复现

`FastArchitectureFeatures`新增只需Gap值的特征入口；原PDB入口仍使用同样的运算。`FastResidualModel`共享树求值内核，模板修正允许负值。扩展后V53完整150053条输出不变。

运行`scripts/run_v56_template_correction.py --wait-pid <V54 CPU pipeline pid>`。C++入口：`build/core_template_estimate -in requests.csv -out results.csv --model core-template-zlib.bin --residual-model correction.bin --trees 256 --no-cache`。

## 文献及边界

- [Prokhorenkova等，CatBoost 2018](https://arxiv.org/abs/1706.09516)：数值对称残差树，延续V50依据。
- [Marquardt等，FPGA 2000](https://www.eecg.toronto.edu/~jayar/pubs/marq/fpga2000_arm.pdf)：位移模板参考。
- 压缩分解依据及逐值核对见V55方法报告。

新研究点是已压缩核心架构模板与有符号误差校正的组合，所有组成技术已有先例。需要比较与V53的真实精度/时间/空间，不以方案更复杂宣称有创新效果，也没有V40的逐请求证书。
