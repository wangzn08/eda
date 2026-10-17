"""Normalized robust local affine residuals; development-only fitting."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v162';out.mkdir(exist_ok=True)
a=z['a'].astype(np.float32);av=z['av'].astype(np.float32);cats=[80,94,99,100,107]
mean=a.mean(axis=0,dtype=np.float64);std=a.std(axis=0,dtype=np.float64);std=np.maximum(std,1e-6)
mean[cats]=0;std[cats]=1
a=((a-mean)/std).astype(np.float32);av=((av-mean)/std).astype(np.float32)
np.savez(out/'normalization.npz',mean=mean,std=std)
r={'state':'running','fit_split':'development','holdout_used':False,'scope':'Normalized robust linear-leaf prototype; native inference not profiled','categories':cats,'candidates':[]};start=time.monotonic()
for objective,leaves,trees,regularization in [('huber',127,16,1),('huber',255,32,10),('fair',127,32,10),('regression',127,32,10)]:
 name=f'{objective}-{leaves}-{trees}-{regularization}'
 ds=lgb.Dataset(a,label=z['y']-z['b'],weight=1000/np.maximum(z['y'],1),categorical_feature=cats,params={'linear_tree':True})
 m=lgb.train({'objective':objective,'linear_tree':True,'linear_lambda':regularization,'learning_rate':.1,'num_leaves':leaves,'min_data_in_leaf':100,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007},ds,num_boost_round=trees)
 m.save_model(str(out/f'{name}.txt'))
 p=np.rint(np.maximum(0,z['bv']+m.predict(av,num_threads=1)));np.save(out/f'{name}.npy',p)
 item={'name':name,'score':score(z['yv'],p),'model_bytes':(out/f'{name}.txt').stat().st_size,'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True)
 (ROOT/'reports/V162-normalized-linear-leaf.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V162-normalized-linear-leaf.json').write_text(json.dumps(r,indent=2)+'\n')
