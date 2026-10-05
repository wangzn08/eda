"""Compare periodic representatives; all candidates approximate, no certificates."""
import csv,json,subprocess,time
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
_,y,_,_=load('validation')
def read(path):
    with path.open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
def loss(p):return np.tanh(4*np.abs(p-y)/np.maximum(y,1))
base=read(ROOT/'out/evaluation/validation.v55-core.csv');corrected=read(ROOT/'out/evaluation/validation.v59-profile.csv')
best=loss(base);best_with_correction=loss(corrected);items=[]
for sx,sy in ((0,0),(1,0),(0,1),(1,1),(2,0),(0,2),(2,2)):
    name=f'v61-shell-{sx}-{sy}';out=ROOT/f'out/evaluation/{name}.csv'
    args=['build/core_template_estimate','--model','out/architecture-benchmark/core-template-zlib.bin','--shell-x',str(sx),'--shell-y',str(sy),'--no-cache','-in','out/evaluation/validation.request.csv','-out',str(out)]
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,check=True)
    (ROOT/f'out/{name}.log').write_text(result.stderr)
    p=read(out);assert len(p)==len(y)
    l=loss(p);best=np.minimum(best,l);best_with_correction=np.minimum(best_with_correction,l)
    items.append({'shell_x':sx,'shell_y':sy,'score':float(100*(1-l.mean())),
                  'different_from_original_fraction':float(np.mean(p!=base)),
                  'process_log':result.stderr.strip()})
report={'holdout_used':False,'candidates':items,'oracle_best_shell_score':float(100*(1-best.mean())),
        'oracle_best_shell_or_v59_score':float(100*(1-best_with_correction.mean())),
        'scope':'Golden-based selection is only a candidate-diversity ceiling; no trained selector, no certified upper bound or throughput acceptance.'}
(ROOT/'reports/V61-template-shell-candidates.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
