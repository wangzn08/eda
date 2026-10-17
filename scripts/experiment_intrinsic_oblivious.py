"""Symmetric-tree challenger using architecture diagnostics, development labels only."""
import json,time,numpy as np
from catboost import CatBoostRegressor
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v129';out.mkdir(exist_ok=True);start=time.monotonic();r={'state':'running','fit_split':'development','holdout_used':False,'scope':'Python prototype; deployment and throughput unverified','candidates':[]}
for depth,iterations in ((6,600),(10,600)):
 m=CatBoostRegressor(iterations=iterations,depth=depth,learning_rate=.08,loss_function='MAE',thread_count=1,random_seed=20261007,verbose=False,allow_writing_files=False)
 m.fit(z['a'],z['y']-z['b'],sample_weight=1000/np.maximum(z['y'],1));m.save_model(str(out/f'depth{depth}.cbm'))
 for prefix in (100,300,600):
  p=np.rint(np.maximum(0,z['bv']+m.predict(z['av'],ntree_end=prefix,thread_count=1)));np.save(out/f'depth{depth}-{prefix}.npy',p);i={'depth':depth,'trees':prefix,'score':score(z['yv'],p),'elapsed_seconds':time.monotonic()-start};r['candidates'].append(i);print(json.dumps(i),flush=True)
 (ROOT/'reports/V129-intrinsic-oblivious-models.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V129-intrinsic-oblivious-models.json').write_text(json.dumps(r,indent=2)+'\n')
