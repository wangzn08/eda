"""Summarize coupled validation/novel-input measurements and score tradeoffs."""
import json
from architecture import ROOT

base=json.loads((ROOT/'reports/V242-novel-request-profile.json').read_text())
old=json.loads((ROOT/'reports/V242-joint-goal-profile.json').read_text())
def proxy(accuracy,seconds):return .8*accuracy+15*max(0,1-seconds/1800)+5
seconds=base['pooled_billion_estimate_cpu_seconds_including_initialization']
lines=['# V253 / V254：本轮结果与选择','','日期：2026-10-19。对照基准为V242的新请求测量，不使用其重复请求约9分钟的时间。','','## 同一程序的实测与外推','','| 配置 | 完整验证分 | 平均CPU微秒/条 | 十亿CPU外推，含初始化 | 本机技术分估算* |','| --- | ---: | ---: | ---: | ---: |',f"| V242基准 | {old['validation_score']:.10f} | {base['pooled_query_cpu_seconds_per_request']*1e6:.6f} | {seconds/60:.4f}分钟 | {proxy(old['validation_score'],seconds):.4f} |"]
ready=[]
for version,label in [(250,'较高验证分参考'),(251,'直接候选存储参考'),(253,'短专家'),(254,'保持原预测、优化引擎')]:
 r=json.loads((ROOT/f'reports/V{version}-native-score-profile.json').read_text())
 t=r.get('pooled_billion_estimate_cpu_seconds');accuracy=r.get('validation_score')
 if t is None:continue
 suffix='' if r['state']=='complete' else '（单轮速度初筛）'
 lines.append(f"| V{version} {label}{suffix} | {accuracy:.10f} | {r['pooled_query_cpu_seconds_per_request']*1e6:.6f} | {t/60:.4f}分钟 | {proxy(accuracy,t):.4f} |")
 if version in (253,254) and r['state']=='complete':ready.append((proxy(accuracy,t),version))
lines+=['','*本机技术分估算：`0.8×验证分 + 0.15×100×max(0,1−CPU外推秒/1800) + 0.05×100`。暂设一致性100分；没有把两个不同速度输入当作官方五次相同输入一致性测量。使用验证分及CPU外推代替官方隐藏集结果，因此这些不是官方成绩。','','30分钟以内，十亿CPU用时每减少60秒，估算技术分增加0.5；验证分增加0.02只贡献0.016。因此较大模型取得更高验证分，不一定得到更高综合技术分。','']
if len(ready)==2:
 recommended=max(ready)[1];lines += [f'按上述本机口径推荐 **V{recommended}**；V253保留为验证分更高、速度略慢的配置。','']
else:lines += ['第二轮速度测量尚未全部完成，暂不将初筛当作冻结结果。','']
lines+=['## 方案实际使用了什么','','- V254沿用V242的137特征、8树残差与浅门控；完整验证输出保持不变。中间架构算子缓存关闭。','- V253使用两个按跨墙几何选择的8树专家，仍是137特征；更强的浅门控对容易请求提前结束。187维物理交互特征、更宽模型、更多场景及相对误差表示均做过对照，最终没有用于这版短专家。','- 两版先按区间界形成安全候选，再只在剩余候选上枚举完整有限位移域，保留所有位移的第一个最小项。精确性针对有限响应银行，不是声称真实图最短路精确。','- 为候选表预留同一内存映射，按整行暂存、反向原地扩展为1/3字节掩码，避免查询时再读候选字典。源代码保留共享小集合编码作为对照，但V253/V254使用的是直接掩码。','- V253在批内按专家分组计算，最后按原输入顺序写出；V254采用32行原顺序流水线。两版均保留目标响应的批量预取和整数编译树。','','## 测量范围','','- Apple M4/macOS，单线程标准入口，输入输出CSV均计入查询CPU。','- 固定150053条validation用于评分；新请求没有真实延时标签，只用于吞吐测量。','- 新请求总计600万条，来自独立重新组合development起终点，排除development/validation已知请求对，全部互不重复。分两份，各300万条。没有读取holdout。','- 每条耗时为批量平均CPU，不是逐次启动程序的一条请求响应延迟。初始化每次启动进行一次，已计入十亿外推。','- 没有实际运行十亿条；其他输入分布、评测机器及长时间持续吞吐需另测。','']
for v in (250,253,254):
 audit_path=ROOT/f'reports/V{v}-submission-audit.json'
 if audit_path.exists():
  audit=json.loads(audit_path.read_text());lines += [f'## V{v} 交付证据','',f"完整目录 {audit['complete_submission_bytes']:,} bytes，峰值RSS {audit['peak_rss_bytes']:,} bytes；全部运行资产与实测SHA一致。独立重编译所有文件支持的Mach-O节相同，仅UUID与签名不同，交付恢复为实测原始程序。",'',f'目录：`out/submission/final-v{v}/`；压缩包：`out/submission/fpga-delay-v{v}.tar.gz`。', '',f'完整指标：`reports/V{v}-native-score-profile.json`；交付审计：`reports/V{v}-submission-audit.json`。','']
lines+=['## 构建与使用','','```sh','make','build/runtime-v254/estimate -in /absolute/path/request.csv -out /absolute/path/result.csv','make runtime-v253','build/runtime-v253/estimate -in /absolute/path/request.csv -out /absolute/path/result.csv','make runtime-v250','```','','V250保留较高验证分，需要Python3标准库从模型生成临时树代码；V253/V254的树代码已直接包含。原重复请求版本可用`make runtime-v242`重编译。','','论文引用、全部失败方向和创新边界见`reports/V243-V251-research-progress.md`及`papers/README.md`。不把GBDT、专家模型、门控或位压缩本身作为原创理论。','']
(ROOT/'reports/V253-V254-final.md').write_text('\n'.join(lines))
print('reports/V253-V254-final.md')
