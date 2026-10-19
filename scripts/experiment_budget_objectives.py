"""Compare compact single-tree objectives and a distilled small forest."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from native_research_labels import load_labels
out=ROOT/'out/v291';out.mkdir(exist_ok=True);x=np.load(ROOT/'out/v288/features.npy');b=np.load(ROOT/'out/v276/base.npy');z=load_labels();y,yv=z['y'],z['yv'];n=len(y);w=1000/np.maximum(y,1)
(out/'port-metadata.json').write_bytes((ROOT/'out/v288/port-metadata.json').read_bytes())
teacher=lgb.Booster(model_file=str(ROOT/'out/v288/eight511.txt'));soft=teacher.predict(x[:n],num_threads=1)
report={'state':'running','fit_scope':'development only, objective comparison and forest-to-single-tree distillation','holdout_used':False,'candidates':[]}
for name,obj,target,extra in [('mse','regression',y-b[:n],{}),('huber','huber',y-b[:n],{'alpha':.9}),('fair1','fair',y-b[:n],{'fair_c':1}),('fair3','fair',y-b[:n],{'fair_c':3}),('student','regression',soft,{})]:
 for leaves in (1023,4095):
  start=time.monotonic();m=lgb.train({'objective':obj,'num_leaves':leaves,'max_depth':24,'min_data_in_leaf':40,'learning_rate':1,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019,**extra},lgb.Dataset(x[:n],label=target,weight=w),num_boost_round=1);key=f'{name}-{leaves}';m.save_model(str(out/f'{key}.txt'));d=m.predict(x[n:],num_threads=1)
  # Validation-only candidate selection, not an independent generalization score.
  for cutoff in (0,1,2):
   delta=np.where(abs(d)<=cutoff,0,d);p=np.rint(np.maximum(0,b[n:]+delta));score=float(100*np.mean(1-np.tanh(4*abs(p-yv)/np.maximum(yv,1))));np.save(out/f'{key}-c{cutoff}.npy',p);item={'name':key,'cutoff':cutoff,'score':score,'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True)
  (ROOT/'reports/V291-objectives.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V291-objectives.json').write_text(json.dumps(report,indent=2)+'\n')
