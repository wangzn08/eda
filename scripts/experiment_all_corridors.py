"""Architecture-only all-crossing corridor ablation; no model fitting."""
import json,csv,subprocess,numpy as np,time
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v122';_,y,_,_=load('development');_,yv,_,_=load('validation');r={'state':'running','holdout_used':False,'fit_labels_used':False,'scope':'Full development and validation, not final throughput','candidates':[]}
for mode in (1,2,3):
 dest=out/f'mode{mode}.csv';log=out/f'mode{mode}.stderr'
 with log.open('w') as f:subprocess.run(['/usr/bin/time','-l',str(out/'estimate'),'--all-corridors',str(mode),'-in','out/v117/all.request.csv','-out',str(dest)],cwd=ROOT,stderr=f,check=True)
 p=np.loadtxt(dest,delimiter=',',skiprows=1,usecols=2,dtype=np.int64);assert len(p)==len(y)+len(yv);item={'mode':mode,'development_score':score(y,p[:len(y)]),'validation_score':score(yv,p[len(y):])};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V122-all-corridors.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V122-all-corridors.json').write_text(json.dumps(r,indent=2)+'\n')
