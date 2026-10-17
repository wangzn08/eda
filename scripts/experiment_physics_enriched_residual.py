"""Expose late-transient and nine-anchor responses to residual learners."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v164';out.mkdir(exist_ok=True)
from physics_response_features import enrich
a=enrich(z['a']);av=enrich(z['av']);start=time.monotonic();r={'state':'running','fit_split':'development','holdout_used':False,'features':a.shape[1],'physics_tables':'Architecture-only finite ideal-graph tail and multianchor responses; approximate descriptors, not true physical shortest-path certificates','scope':'Accuracy prototype; native timing/budget pending','candidates':[]}
for name,leaves,trees in [('small',127,64),('large',511,256)]:
 ds=lgb.Dataset(a,label=z['y']-z['b'],weight=1000/np.maximum(z['y'],1));m=lgb.train({'objective':'regression_l1','num_leaves':leaves,'min_data_in_leaf':30,'learning_rate':.07,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007},ds,num_boost_round=trees);m.save_model(str(out/f'{name}.txt'))
 p=np.rint(np.maximum(0,z['bv']+m.predict(av,num_threads=1)));np.save(out/f'{name}.npy',p);item={'name':name,'score':score(z['yv'],p),'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V164-physics-enriched-residual.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V164-physics-enriched-residual.json').write_text(json.dumps(r,indent=2)+'\n')
