"""Write the acceptance summary from measured results; never imply hidden-set speed."""
import json
from architecture import ROOT

def main():
    path=ROOT/'reports/V14-acceptance.json';r=json.loads(path.read_text())
    assert r['phase']=='complete' and len(r['billion_runs'])==5
    p=json.loads((ROOT/'reports/V14-package-acceptance.json').read_text())
    c=r['checks'];runs=r['billion_runs'];expected=json.loads((ROOT/'out/acceptance-v14/expected-repeat.json').read_text())
    assert all(x['sha256']==expected['expected_sha256'] for x in runs)
    new=c['public-million']['cpu_seconds']*1000
    r.update(expected_repeated_output_matches=True,
        new_query_billion_linear_estimate_seconds=new,
        new_query_billion_measured=False,
        official_environment_verified=False,
        acceptance_conclusion='Local pipeline and repeated public billion pass; unique-query throughput is not compliant by linear estimate; final hidden-set acceptance remains unverified.')
    path.write_text(json.dumps(r,indent=2)+'\n')
    rows='\n'.join(f"| {x['index']} | {x['cpu_seconds']:.3f} | {x['wall_seconds']:.3f} | {x['peak_rss_bytes']/1e6:.2f} |" for x in runs)
    text=f'''# V14 本机完整流程验收

日期：2026-10-04；环境：{r['machine']}。独立压缩包解压后以 C++17/O3 重编译，再使用默认 V14 标准 `-in/-out` 命令验收。模型和路径资源在留出评分前冻结。

## 结论

本机数据处理、构建、独立打包、预测、评分和重复一致性流程通过。公开百万请求重复1000次的十亿条测试五轮均在时间及内存限制内。**尚不能判定最终比赛验收通过：全新请求速度不足，且 Linux 官方评测环境未验证。** 本轮没有重新训练或依据留出集选择模型。

## 准确性与功能

| 项目 | 结果 |
|---|---:|
| 验证集150,053条官方公式分 | {c['validation']['metrics']['positive_delay_score']:.8f} |
| 冻结后留出集149,242条官方公式分 | {c['holdout']['metrics']['positive_delay_score']:.8f} |
| 公开全集1,000,000条分（包含开发数据） | {c['public-million']['metrics']['positive_delay_score']:.8f} |
| 留出集相对误差中位数 | {100*c['holdout']['metrics']['relative_error_p50']:.4f}% |
| 留出集相对误差P95 | {100*c['holdout']['metrics']['relative_error_p95']:.4f}% |
| 留出集答案完全相等 | {c['holdout']['metrics']['exact_matches']:,} / 149,242 |

这里的97.21是连续误差评分，不是97.21%的请求完全相等。零延时官方公式除零处理未定义；公开集唯一零延时样本预测正确，单独报告、不计入公式均值。

- 原有6项评分/几何单元测试通过；官方8条精确参考检查8/8，单向/双向输出一致；开发样本、同点及重复请求检查11/11。
- 这些8/8结果属于精确参考求解器，不表示 V14 所有样本都精确。
- V14 开启和关闭预测缓存的验证输出 SHA-256 完全相同。
- 解压后源码及资源与清单逐文件哈希一致。实际预测不读取 golden；缓存只保存本进程计算的预测值。

## 十亿条重复测试

输入仅包含 From,To，是公开百万请求按原顺序重复1000次；每轮进程重新启动、缓存重新构建。实际运行十亿行，而非小样本乘倍数。输出约40.33GB，各轮哈希同时与百万预测输出重复1000次的预期哈希相等。

| 轮次 | CPU秒 | 墙钟秒 | 峰值RSS MB |
|---|---:|---:|---:|
{rows}

平均CPU：**{r['average_billion_cpu_seconds']:.3f}秒**；时间分：{r['time_score']:.4f}。按留出准确分估算技术总分为{r['local_simulated_total']:.4f}，仅是本机模拟，不是官方打榜分。每轮缓存命中999,000,000条，未命中1,000,000条。

输出 SHA-256：`{runs[0]['sha256']}`。

## 全新请求的性能限制

公开百万条请求均不重复，实测 CPU **{c['public-million']['cpu_seconds']:.3f}秒**，约45.884微秒/条。若十亿条都需要首次预测，线性估算为 **{new:.0f}秒，约{new/3600:.2f}小时**，超过1小时限制。这个数字是估算，未运行十亿条全新请求。最终隐藏集的重复率未知，不能用上面的缓存测试宣称正式性能达标。

后续必须压缩/蒸馏模型或降低每条新请求的计算成本，评估速度与准确性的取舍；99分目标尚未达到。

## 提交大小与可移植性

- 上传压缩包：{p['archive_bytes']/1e6:.2f}MB，低于100MB（按十进制计算）。
- 当前 macOS 可执行文件和两个必需资源合计：{p['runtime_bytes']/1e6:.2f}MB。
- 解压全部文件含源码、内嵌模型文本及二进制重复内容：{p['all_bundle_bytes']/1e6:.2f}MB，**超过100MB**；上述通过结论针对上传压缩文件。若官方限制解压总量，须调整交付内容。
- macOS arm64 二进制不能直接作为 Linux 二进制使用；包内有 C++17 源码，但 Linux 编译与官方机计时未完成。
- 大型验收输入/输出结束后清理；保留预测小文件、日志、哈希、资源和复现脚本。

压缩包 SHA-256：`{p['archive_sha256']}`。

## 复现

```sh
python3 scripts/package_v14.py
# 将压缩包解压至 out/acceptance-v14/extracted 并在包目录执行：
c++ -std=c++17 -O3 estimate.cpp -o estimate
# 返回仓库目录，完成公开请求与固定划分准备后：
python3 scripts/accept_v14.py
python3 scripts/prepare_v14_billion.py
python3 scripts/accept_v14.py --billion-only
```

数据明细：[验收JSON](V14-acceptance.json)、[包清单](V14-package-acceptance.json)。模型方法及参考论文见[研究报告](V9-V14-architecture-route-research.md)与[论文笔记](../papers/README.md)。
'''
    (ROOT/'reports/V14-final.md').write_text(text)

if __name__=='__main__':main()
