"""Architecture-derived top-four candidates; development-only residual fit."""
import json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v144';start=time.monotonic();c=np.loadtxt(out/'branches.csv',delimiter=',',dtype=np.float64);n=len(z['y']);assert c.shape==(n+len(z['yv']),70);expected=np.concatenate((z['b'],z['bv']));assert np.array_equal(c[:,0],expected),'Candidate collection changed baseline'
raw=c[:,1:].copy()
for k in range(4):
 j=1+17*k;valid=raw[:,j]>=0;raw[valid,j]-=c[valid,0];raw[:,j]=np.clip(raw[:,j],-1,10000)
a=np.column_stack((z['a'],raw[:n])).astype(np.float32);av=np.column_stack((z['av'],raw[n:])).astype(np.float32);np.savez(out/'fit-features.npz',a=a,av=av,y=z['y'],yv=z['yv'],b=z['b'],bv=z['bv'])
r={'state':'running','fit_split':'development','holdout_used':False,'baseline_parity':True,'features':a.shape[1],'scope':'Architecture candidate-set feature screening; not native speed or submission','candidates':[]}
for name,leaves,trees in [('single',4095,1),('shared',511,256)]:
 ds=lgb.Dataset(a,label=z['y']-z['b'],weight=1000/np.maximum(z['y'],1));m=lgb.train({'objective':'regression_l1','learning_rate':1 if trees==1 else .07,'num_leaves':leaves,'min_data_in_leaf':30,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007},ds,num_boost_round=trees);m.save_model(str(out/f'{name}.txt'))
 for prefix in ([1] if trees==1 else [32,64,128,256]):
  p=np.rint(np.maximum(0,z['bv']+m.predict(av,num_iteration=prefix,num_threads=1)));np.save(out/f'{name}-{prefix}.npy',p);i={'name':name,'trees':prefix,'score':score(z['yv'],p),'elapsed_seconds':time.monotonic()-start};r['candidates'].append(i);print(json.dumps(i),flush=True)
 (ROOT/'reports/V144-candidate-set-residual.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V144-candidate-set-residual.json').write_text(json.dumps(r,indent=2)+'\n')
