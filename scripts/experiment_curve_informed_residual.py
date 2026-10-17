"""Exact finite-ideal-graph curves and obstruction geometry as residual features."""
import json,lzma,struct,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from physics_response_features import enrich
from experiment_v7_teacher import score
from curve_response_features import features
z=np.load(ROOT/'out/v125/fit-features.npz');a=features(z['a']);av=features(z['av']);out=ROOT/'out/v170';out.mkdir(exist_ok=True);start=time.monotonic();r={'state':'running','fit_split':'development','holdout_used':False,'features':a.shape[1],'scope':'Curve/obstruction-conditioned accuracy prototype; native inference and budget pending','candidates':[]}
for name,leaves,trees in [('compact',511,256),('wide',1023,512)]:
 ds=lgb.Dataset(a,label=z['y']-z['b'],weight=1000/np.maximum(z['y'],1));m=lgb.train({'objective':'regression_l1','num_leaves':leaves,'min_data_in_leaf':30,'learning_rate':.07,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007},ds,num_boost_round=trees);m.save_model(str(out/f'{name}.txt'))
 p=np.rint(np.maximum(0,z['bv']+m.predict(av,num_threads=1)));np.save(out/f'{name}.npy',p);item={'name':name,'score':score(z['yv'],p),'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V170-curve-informed-residual.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V170-curve-informed-residual.json').write_text(json.dumps(r,indent=2)+'\n')
