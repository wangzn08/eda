"""Summarize only measured, same-program accuracy/runtime combinations."""
import csv,json,platform,re
from pathlib import Path
import numpy as np
from architecture import ROOT
from native_research_labels import load_labels

def read(path):return json.loads((ROOT/path).read_text())
def predictions(path):
 with (ROOT/path).open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)

v=274;final=read(f'reports/V{v}-native-score-profile.json');audit=read(f'reports/V{v}-submission-audit.json');package=read(f'reports/V{v}-submission-integrity.json')
assert final['state']=='complete' and audit['state']=='complete'
assert len(final['runs'])==3 and all(r['billion_estimate_cpu_seconds']<=3600 for r in final['runs'][1:])
old=read('reports/V254-native-score-profile.json');y=load_labels()['yv'].astype(float);assert np.all(y>0)
a=predictions('out/v254/score-profile/validation.csv');b=predictions(f'out/v{v}/score-profile/validation.csv')
la=np.tanh(4*abs(a-y)/y);lb=np.tanh(4*abs(b-y)/y);tail=np.argsort(la)[-int(len(y)*.01):]
error={'state':'complete','validation_rows':len(y),'old_version':254,'new_version':v,'score_gain':float(100*np.mean(la-lb)),'relative_deduction_reduction':float(1-lb.mean()/la.mean()),'old_exact_fraction':float(np.mean(a==y)),'new_exact_fraction':float(np.mean(b==y)),'improved_rows':int(np.sum(lb<la)),'worsened_rows':int(np.sum(lb>la)),'unchanged_rows':int(np.sum(lb==la)),'old_worst_1pct_loss_share':float(la[tail].sum()/la.sum()),'old_worst_1pct_loss_reduction':float(1-lb[tail].sum()/la[tail].sum()),'old_absolute_error_quantiles':np.quantile(abs(a-y),[.5,.9,.95,.99,.999,1]).tolist(),'new_absolute_error_quantiles':np.quantile(abs(b-y),[.5,.9,.95,.99,.999,1]).tolist(),'quantile_levels':[.5,.9,.95,.99,.999,1],'holdout_used':False}
(ROOT/f'reports/V{v}-error-summary.json').write_text(json.dumps(error,indent=2)+'\n')
def proxy(p):
 if any(r['billion_estimate_cpu_seconds']>3600 for r in p['runs'][1:]):return None
 return .8*p['validation_score']+15*max(0,1-p['pooled_billion_estimate_cpu_seconds']/1800)+5
table=[]
for version in (254,260,264,267,272,274):
 p=read(f'reports/V{version}-native-score-profile.json');time=p['pooled_billion_estimate_cpu_seconds'];score=proxy(p);n=len(p['runs'])-1
 table.append(f"| V{version} | {p['validation_score']:.10f} | {time/60:.4f}分钟 | {n}批 | "+('超一小时，不能提交' if score is None else f'{score:.4f}')+' |')
log=(ROOT/f'out/v{v}/score-profile/validation.stderr').read_text();selected=int(re.search(r'endpoint_profile_evaluations=(\d+)',log)[1]);seconds=final['pooled_billion_estimate_cpu_seconds']
text=f'''# V255–V274：精度专项迭代

日期：2026-10-19。用户要求继续提高精度。最终保留V274高精度配置，完整150053条验证分 **{final['validation_score']:.10f}**；相对默认V254的99.5061105063，提高 **{error['score_gain']:.6f}分**，扣分减少 **{100*error['relative_deduction_reduction']:.2f}%**。验证分是相对误差评分，不是完全预测正确的比例。

## 同一程序的结果与取舍

| 配置 | 完整原生验证分 | 十亿新请求CPU外推，含初始化 | 实际测速 | 本机技术分估算* |
| --- | ---: | ---: | --- | ---: |
{chr(10).join(table)}

*仅用完整validation和本机合成新请求CPU外推代入官方公式，暂设一致性100；没有进行官方五轮相同十亿输入测量。超一小时版本按规则不能作为有效提交，未替它计算有效技术分。V267/V272只有一批测速筛选，不称为完整冻结交付。

**V274提高了精度，但本机综合分估算仍低于V254。** 因此`make`继续构建综合优先的V254，`make runtime-accuracy`构建V274。两者独立保留，未把高精度版的分数与快速版的耗时合并。

V274两次独立测速外推分别为 **{final['runs'][1]['billion_estimate_cpu_seconds']:.4f} / {final['runs'][2]['billion_estimate_cpu_seconds']:.4f}秒**，平均 **{seconds/60:.4f}分钟**。批量平均查询CPU为 **{final['pooled_query_cpu_seconds_per_request']*1e6:.6f}微秒/条**。每批实际300万条，全部来自同一份既有600万互不重复新配对请求清单；没有十亿实跑，也没有新请求真实标签。M4/macOS单线程本机结果不保证适用于官方Linux、其他机器或隐藏输入分布。

逐条完全相等比例从{error['old_exact_fraction']*100:.4f}%升到{error['new_exact_fraction']*100:.4f}%，P99绝对误差55→41ps，原最差1%请求的扣分减少{error['old_worst_1pct_loss_reduction']*100:.2f}%。仍有{error['worsened_rows']}条验证请求退化，最大绝对误差289→341ps；总体评分提升不代表每一条请求都更准。

## 新架构

1. 原物理估算先得到候选路径及137个几何、曲线、边界势特征。
2. 一个16树的小型分流模型预测复杂修正的预期误差收益。本版使用原始收益门控，不是工作量归一化门控。收益标签来自development的两折交叉拟合；分流模型和专家训练都不使用validation标签。验证只用于比较候选和阈值。
3. 收益不够的请求继续使用冻结V254的8树及原浅门控。其他请求在起点和终点各展开至多两步实际合法有向连接，保留宽度2的候选，再用有限理想响应银行估计中间段。形成16个局部路径差值、候选间距和入口费用特征。
4. 根据是否跨越垂直障碍，选择一个32树专家修正。只运行所属专家，不累加两个专家；每条还包括分流模型成本。复杂分支计算原验证中触发 **{selected}/{len(y)}，即{selected/len(y)*100:.4f}%**。
5. 标准入口把“直接输出/快速修正/物理专家”决定保存在批内，只计算一次分流，按原始输入顺序输出。中间算子缓存和最终预测缓存均关闭。

局部连接来自真实图，但beam截断和有限理想中间段均近似；不能称为真实图的精确最短路或可采纳下界。本轮完整验证及两批速度输入均由同一冻结可执行文件完成，所有运行资产前后SHA一致。

## 做过的不同方向

- V255：双端实际连接和有限银行合成的新特征，最高原生32树/专家为99.6773156；全量调用耗时过高，只作为研究对照。64树/专家的离线99.6789627未做同版原生交付。
- V256：对称树、类别有序统计、深度8/10三个CatBoost配置，最高离线99.4919014，未采用。换树结构并未超过路径特征方案。
- V257：直接用source2、双端组合等物理量作回归基准，最高离线99.6688293，未超过原基准加路径特征。
- V258：只围绕已选路径展开，并分别去掉终点/起点/二阶计算；最高离线99.6156740，较便宜但损失精度。
- V259：不做新增路径展开，在已有源候选上合并边界势包络，最高离线99.5387241，未采用。
- V263：合并同源响应行准备；850758行全部基线和16特征逐字节不变。没有把并行研究期间的导出耗时当作最终加速证据。
- V265：更宽的1023/2047叶专家没有显著提高分数，未增加最终提交的模型体积。
- V266：从原估算中保存候选种子，避免完整重排全部起终点；最高离线99.6590771，未替换最终完整候选专家。
- V262/V269/V271：比较二元收益门控、直接收益回归、按候选工作量归一化门控，以及4/8/16树收益模型。最终选择以原生同版结果为准。
- V273：邻近路径成本校准的小范围离线筛选最高99.6795275，尚未采用到V274；不是已交付的新分数。

每个方向的完整参数、分数和未采用结果均在对应JSON，版本空号不代表做过未记录的实验。本轮不读取holdout。

## 文献与创新边界

- Bellman, *On a routing problem*, 1958：[题录](https://doi.org/10.1090/qam/102435)，[扫描原文](https://www.cs.yale.edu/homes/lans/readings/routing/bellman-routing-1958.pdf)。采用经典的“当前合法边费用加后续费用再取最小”递推思想。本文与本程序的有限后缀/beam近似不同，不将其最短路结论直接套用到本程序；本轮只核对题录与扫描文档信息，未声称通读全文。
- Ke等, [LightGBM, NeurIPS2017](https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html)：已有提升树实现，负责残差和分流模型。
- Wang等, [IDK Cascades, UAI2018](https://proceedings.mlr.press/r16/wang18c.html)：按输入分配不同推理计算的参考；这里不是复现其分类系统。
- Prokhorenkova等, [CatBoost, NeurIPS2018](https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html)：作为独立对称树/类别模型对照；本轮核对官方摘要并运行开源实现，未声称复现论文benchmark。

工程创新候选是把双端真实局部连接、有限响应银行、跨墙专家与交叉拟合收益分流组合，并复用批内决策。动态规划、beam search、提升树、交叉拟合和级联本身均不是本项目原创。没有据此声称全球首次或保证竞赛排名。

## 交付证据

- 完整提交：`out/submission/final-v274/`，**{package['complete_submission_bytes']:,} bytes**，包括程序、五份模型/架构资产、许可证、源码、构建脚本与说明。
- 峰值RSS：**{final['peak_rss_bytes']:,} bytes**；两轮单线程外推均小于3600秒。
- 压缩包：`out/submission/fpga-delay-v274.tar.gz`，{package['archive_bytes']:,} bytes；SHA256 `{package['archive_sha256']}`。
- 独立源码重编译所有文件支持的Mach-O节一致，只允许UUID与签名差异；交付恢复为实际测量过的原始可执行文件。
- 原始记录：`reports/V274-native-score-profile.json`；交付/重建：`reports/V274-submission-integrity.json`、`reports/V274-submission-audit.json`；逐行误差变化：`reports/V274-error-summary.json`。

## 使用与复现

```sh
make                         # 综合优先，冻结V254
make runtime-accuracy        # 精度优先，冻结V274
build/runtime-v274/estimate -in /absolute/path/request.csv -out /absolute/path/result.csv
```

本地完整包可在目录中`make rebuild`；只需C++17、zlib、liblzma和Python3标准库，不需要LightGBM、CatBoost或训练数据。预编译程序为M4/macOS ARM64，Linux需重编译，性能未测。

Git中的`artifacts/runtime-v274/`为轻量快照，和`artifacts/runtime-v219/`共用不变架构文件。可用`python3 scripts/assemble_score_release.py --version 274 --output out/submission/reassembled-v274`组装。整个Git仓库大小不是提交包大小。

训练研究需要官方数据和既有`out/evaluation/development.request.csv`、`validation.request.csv`及对应golden。`scripts/native_research_labels.py`优先读取历史标签缓存，缺失时直接读取这两个golden，不依赖旧137特征拟合文件。可以先组装冻结V242，再运行`export_native_research_features.py --runtime <V242目录> --output out/v243`重建原生137维特征；该脚本拒绝覆盖已有导出。之后用`probe_endpoint_bellman.cpp`导出16维双端特征，再依次运行`experiment_endpoint_bellman.py`、`experiment_bellman_cascade.py`、`experiment_boosted_gain_gates.py`。工作量对照还需V259计数字段，见对应脚本；不能将缺失缓存默认为已完成实验。
'''
(ROOT/'reports/V255-V274-accuracy.md').write_text(text)
print(json.dumps({'version':v,'score':final['validation_score'],'minutes':seconds/60,'score_proxy':proxy(final),'old_score_proxy':proxy(old),'deduction_reduction_percent':100*error['relative_deduction_reduction'],'submission_bytes':package['complete_submission_bytes'],'peak_rss_bytes':final['peak_rss_bytes']},indent=2))
