"""A small gate forest ranks the expected benefit of expensive path features."""
import csv,json,math
import numpy as np,lightgbm as lgb
from architecture import ROOT
from native_research_labels import load_labels
from experiment_v7_teacher import score
out=ROOT/'out/v271';out.mkdir(exist_ok=True)
z=load_labels();y,yv=z['y'].astype(float),z['yv'].astype(float);n=len(y);x=np.load(ROOT/'out/v255/features.npy',mmap_mode='r');oof=np.load(ROOT/'out/v262/oof.npz');gain=np.tanh(4*abs(oof['old']-y)/np.maximum(y,1))-np.tanh(4*abs(oof['new']-y)/np.maximum(y,1));counts=np.fromfile(ROOT/'out/v259/endpoint.features.bin',dtype=[('b','<i4'),('f','<f4',(16,))])['f'];work=1+counts[:,14]*counts[:,15]/128
columns=list(range(69))+list(range(125,137));(out/'gate-features.json').write_text(json.dumps(columns)+'\n')
old=np.array([int(r['delay']) for r in csv.DictReader((ROOT/'out/v254/score-profile/validation.csv').open())]);new=np.load(ROOT/'out/v255/wall-experts-32.npy')
report={'state':'running','fit_scope':'two-fold development cross-fitted gain; compact gate forest; validation comparison only','holdout_used':False,'candidates':[]}
for name,weighted in [('raw',False),('work',True)]:
 cost=work[:n] if weighted else np.ones(n);gate=lgb.train({'objective':'regression','learning_rate':.3,'num_leaves':127,'max_depth':10,'min_data_in_leaf':250,'num_threads':1,'verbosity':-1,'deterministic':True,'force_col_wise':True,'boost_from_average':False,'seed':20261019},lgb.Dataset(x[:n][:,columns],label=gain/cost,weight=cost),num_boost_round=16)
 for trees in (4,8,16):
  gate.save_model(str(out/f'{name}-{trees}.txt'),num_iteration=trees);value=gate.predict(x[n:][:,columns],num_iteration=trees,num_threads=1)
  for threshold in (.0005,.001,.0015,.002,.0025,.003,.004,.005,.0075,.01):
   selected=value>=threshold;p=np.where(selected,new,old);path=f'{name}-{trees}-t{threshold:g}.npy';np.save(out/path,p)
   item={'gate':name,'trees':trees,'threshold':threshold,'export_threshold':1/(1+math.exp(-threshold)),'score':score(yv,p),'physical_request_fraction':float(np.mean(selected)),'selected_work_proxy_mean':float(np.mean(work[n:]*selected)),'prediction':str((out/path).relative_to(ROOT))};report['candidates'].append(item)
   if .07<=item['physical_request_fraction']<=.15:print(json.dumps(item),flush=True)
   (ROOT/'reports/V271-boosted-gates.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V271-boosted-gates.json').write_text(json.dumps(report,indent=2)+'\n')
