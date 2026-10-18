"""Distill the existing development-trained forest into fewer decision paths."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
out=ROOT/'out/v230';out.mkdir(exist_ok=True);f=np.load(ROOT/'out/v216/fit.npz');z=np.load(ROOT/'out/v125/fit-features.npz');teacher=lgb.Booster(model_file=str(ROOT/'out/v216/tree8.txt'));a=f['a'];av=f['av'];teacher_y=teacher.predict(a,num_threads=1);gold=z['y']-f['b'];w=1000/np.maximum(z['y'],1)
r={'state':'running','fit_scope':'development only; blend development-trained teacher residual and development golden residual','teacher':'out/v216/tree8.txt','holdout_used':False,'candidates':[]}
for name,leaves,trees,lr,blend in [('teacher_one',32767,1,1,1),('teacher_two',8191,2,1,1),('teacher_two_wide',16383,2,.8,1),('teacher_four',4095,4,.7,1),('blend_two',8191,2,1,.5),('blend_four',4095,4,.7,.5)]:
 start=time.monotonic();ds=lgb.Dataset(a,label=blend*teacher_y+(1-blend)*gold,weight=w);m=lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':28,'min_data_in_leaf':20,'learning_rate':lr,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261008},ds,num_boost_round=trees);m.save_model(str(out/(name+'.txt')));p=np.rint(np.maximum(0,f['bv']+m.predict(av,num_threads=1)));np.save(out/(name+'.npy'),p);score=float(100*np.mean(1-np.tanh(4*np.abs(p-z['yv'])/z['yv'])));item={'name':name,'score':score,'trees':trees,'leaves':leaves,'teacher_fraction':blend,'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V230-distilled-selected-trees.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V230-distilled-selected-trees.json').write_text(json.dumps(r,indent=2)+'\n')
