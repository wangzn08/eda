"""Development-only architecture residual models with fewer decision paths."""
import json,time
from pathlib import Path
import numpy as np,lightgbm as lgb
from architecture import ROOT
out=ROOT/'out/v229';out.mkdir(exist_ok=True);f=np.load(ROOT/'out/v216/fit.npz');z=np.load(ROOT/'out/v125/fit-features.npz');a=f['a'];av=f['av'];y=z['y']-f['b'];w=1000/np.maximum(z['y'],1)
r={'state':'running','fit_scope':'development labels only, V216 fixed137-feature schema','holdout_used':False,'candidates':[]}
for name,leaves,trees,lr,minleaf in [('two8191',8191,2,1,15),('four4095',4095,4,.7,15),('two16383',16383,2,.8,15),('two4095',4095,2,1,20)]:
 start=time.monotonic();ds=lgb.Dataset(a,label=y,weight=w);m=lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':28,'min_data_in_leaf':minleaf,'learning_rate':lr,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261008},ds,num_boost_round=trees);m.save_model(str(out/(name+'.txt')));p=np.rint(np.maximum(0,f['bv']+m.predict(av,num_threads=1)));np.save(out/(name+'.npy'),p);score=float(100*np.mean(1-np.tanh(4*np.abs(p-z['yv'])/z['yv'])));item={'name':name,'score':score,'trees':trees,'leaves':leaves,'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V229-fewer-selected-trees.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V229-fewer-selected-trees.json').write_text(json.dumps(r,indent=2)+'\n')
