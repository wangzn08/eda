"""Select frozen candidates only after native time, RSS, size and rebuild checks."""
import argparse,json
from pathlib import Path
from architecture import ROOT
p=argparse.ArgumentParser();p.add_argument('--objective',choices=['accuracy','technical'],default='accuracy');p.add_argument('--output');a=p.parse_args();candidates=[]
for path in sorted((ROOT/'reports').glob('V*-budget-submission.json')):
 r=json.loads(path.read_text());v=r['version'];profile=json.loads((ROOT/f'reports/V{v}-budget-profile.json').read_text())
 if r['state']!='complete' or profile['state']!='complete' or len(profile['runs'])!=3:continue
 if max(r['billion_estimate_cpu_seconds'])>600 or r['peak_rss_bytes']>2000000000 or r['complete_submission_bytes']>100000000:continue
 if r['validation_score']<99 or not r['rebuild_machine_code_identical'] or not r['single_runtime_thread_observed']:continue
 manifest=json.loads((ROOT/f'artifacts/runtime-v{v}/BUILD_MANIFEST.json').read_text())
 assert manifest['runtime_asset_sha256']==profile['asset_sha256_before']==profile['asset_sha256_after']
 # Formal consistency is not measured: this is a local comparison only.
 proxy=.8*r['validation_score']+15*max(0,1-r['pooled_billion_estimate_cpu_seconds']/1800)+5
 candidates.append({'version':v,'validation_score':r['validation_score'],'billion_estimate_cpu_seconds':r['pooled_billion_estimate_cpu_seconds'],'worst_measured_billion_cpu_seconds':max(r['billion_estimate_cpu_seconds']),'complete_submission_bytes':r['complete_submission_bytes'],'technical_proxy_assuming_consistency_100':proxy})
assert candidates,'No fully frozen candidate meets the 600 s budget'
key='validation_score' if a.objective=='accuracy' else 'technical_proxy_assuming_consistency_100';candidates.sort(key=lambda r:(-r[key],r['billion_estimate_cpu_seconds']))
report={'objective':a.objective,'hard_budget_cpu_seconds':600,'selected':candidates[0],'eligible':candidates,'scope':'Local CPU extrapolation on two synthetic novel-request batches, not official judge guarantees; technical comparison assumes consistency=100 without formal five-run proof'}
text=json.dumps(report,indent=2)+'\n'
if a.output:(ROOT/a.output).write_text(text)
print(text,end='')
