"""Increase physics-conditioned teacher capacity; not a submission-speed claim."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from experiment_v7_teacher import score
from physics_response_features import enrich
z=np.load(ROOT/'out/v125/fit-features.npz');a=enrich(z['a']);av=enrich(z['av']);out=ROOT/'out/v166';out.mkdir(exist_ok=True);start=time.monotonic();report={'state':'running','fit_split':'development','holdout_used':False,'scope':'Larger physics-conditioned accuracy teacher; compression and native latency pending','candidates':[]}
for name,leaves,trees in [('wide',1023,1024),('deep',2047,1536)]:
 ds=lgb.Dataset(a,label=z['y']-z['b'],weight=1000/np.maximum(z['y'],1));m=lgb.train({'objective':'regression_l1','num_leaves':leaves,'min_data_in_leaf':20,'learning_rate':.06,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007},ds,num_boost_round=trees,callbacks=[lambda e:print(json.dumps({'training':name,'iteration':e.iteration+1,'elapsed_seconds':time.monotonic()-start}),flush=True) if (e.iteration+1)%128==0 else None]);m.save_model(str(out/f'{name}.txt'))
 for prefix in sorted(set([256,512,1024,trees])):
  p=np.rint(np.maximum(0,z['bv']+m.predict(av,num_iteration=prefix,num_threads=1)));np.save(out/f'{name}-{prefix}.npy',p);item={'name':name,'trees':prefix,'score':score(z['yv'],p),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V166-large-physics-student.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V166-large-physics-student.json').write_text(json.dumps(report,indent=2)+'\n')
