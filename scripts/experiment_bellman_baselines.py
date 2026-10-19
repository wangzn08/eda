"""Residual learning around structural endpoint baselines, not just old output."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from native_research_labels import load_labels
from experiment_v7_teacher import score

out=ROOT/'out/v257';out.mkdir(exist_ok=True)
z=load_labels();y,yv=z['y'].astype(float),z['yv'].astype(float);n=len(y)
x=np.load(ROOT/'out/v255/features.npy',mmap_mode='r');base=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4').astype(float)
report={'state':'running','fit_scope':'development only, full validation comparison; actual local endpoint moves plus approximate suffix','holdout_used':False,'candidates':[]}
params={'objective':'regression_l1','learning_rate':.2,'max_depth':24,'min_data_in_leaf':25,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019}
baselines={'source2':base+x[:,141],'max-source2-target1':base+np.maximum(x[:,141],x[:,140]),'paired11':base+x[:,143]}
for name,b in baselines.items():
 start=time.monotonic();ds=lgb.Dataset(x[:n],label=y-b[:n],weight=1000/np.maximum(y,1));model=lgb.train({**params,'num_leaves':511},ds,num_boost_round=64);model.save_model(str(out/f'{name}.txt'))
 for trees in (8,16,32,64):
  p=np.rint(np.maximum(0,b[n:]+model.predict(x[n:],num_iteration=trees,num_threads=1)));np.save(out/f'{name}-{trees}.npy',p)
  item={'name':name,'trees':trees,'score':score(yv,p),'exact_fraction':float(np.mean(p==yv)),'prediction':f'out/v257/{name}-{trees}.npy','elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True)
  (ROOT/'reports/V257-structural-baselines.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';report['best']=max(report['candidates'],key=lambda v:v['score']);(ROOT/'reports/V257-structural-baselines.json').write_text(json.dumps(report,indent=2)+'\n')
