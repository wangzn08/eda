"""Capacity/rounding screen after adding actual endpoint path information."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from native_research_labels import load_labels
from experiment_v7_teacher import score
out=ROOT/'out/v265';out.mkdir(exist_ok=True)
z=load_labels();y,yv=z['y'].astype(float),z['yv'].astype(float);n=len(y);x=np.load(ROOT/'out/v255/features.npy',mmap_mode='r');b=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4').astype(float)
report={'state':'running','holdout_used':False,'fit_scope':'development-only, fixed32-tree experts, full validation comparison; no native timing claim','candidates':[]}
for name,leaves,rate in [('wide-r20',1023,.2),('wide-r35',1023,.35),('very-wide',2047,.2)]:
 start=time.monotonic();models=[]
 for domain in (0,1):
  m=(x[:n,54]>0)==bool(domain);ds=lgb.Dataset(x[:n][m],label=(y-b[:n])[m],weight=1000/np.maximum(y[m],1));model=lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':28,'min_data_in_leaf':20,'learning_rate':rate,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019},ds,num_boost_round=32);model.save_model(str(out/f'{name}-{domain}.txt'));models.append(model)
 for trees in (8,16,32):
  correction=np.zeros(len(yv))
  for d,model in enumerate(models):
   m=(x[n:,54]>0)==bool(d);correction[m]=model.predict(x[n:][m],num_iteration=trees,num_threads=1)
  p=np.rint(np.maximum(0,b[n:]+correction));np.save(out/f'{name}-{trees}.npy',p)
  item={'name':name,'leaves':leaves,'trees':trees,'score':score(yv,p),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V265-bellman-capacity.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';report['best']=max(report['candidates'],key=lambda v:v['score']);(ROOT/'reports/V265-bellman-capacity.json').write_text(json.dumps(report,indent=2)+'\n')
