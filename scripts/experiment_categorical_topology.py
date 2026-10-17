"""Explicit categorical port-pair/phase interactions, development labels only."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v161';out.mkdir(exist_ok=True);start=time.monotonic()
def features(a):return np.column_stack((a,a[:,80]*496+a[:,94],(a[:,99]+1)*161+a[:,100]+1,(a[:,105]+29)*71+a[:,106]+35)).astype(np.float32)
a=features(z['a']);av=features(z['av']);cats=[77,80,91,94,99,100,107,133,134,135];r={'state':'running','fit_split':'development','holdout_used':False,'scope':'Categorical topology residual prototype; native inference and whole-program timing pending','categories':cats,'reference':'LightGBM official categorical_feature documentation; adapted port-pair and phase categories','candidates':[]}
for name,leaves,trees in [('single',4095,1),('categorical',511,256),('wide',1023,512)]:
 ds=lgb.Dataset(a,label=z['y']-z['b'],weight=1000/np.maximum(z['y'],1),categorical_feature=cats);m=lgb.train({'objective':'regression_l1','learning_rate':1 if trees==1 else .06,'num_leaves':leaves,'min_data_in_leaf':30,'min_data_per_group':10,'cat_smooth':10,'cat_l2':10,'max_cat_to_onehot':4,'max_cat_threshold':32,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007},ds,num_boost_round=trees);m.save_model(str(out/f'{name}.txt'))
 for prefix in sorted(set([trees]+([32,64,128] if trees>1 else []))):
  p=np.rint(np.maximum(0,z['bv']+m.predict(av,num_iteration=prefix,num_threads=1)));np.save(out/f'{name}-{prefix}.npy',p);item={'name':name,'trees':prefix,'score':score(z['yv'],p),'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True)
 (ROOT/'reports/V161-categorical-topology.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V161-categorical-topology.json').write_text(json.dumps(r,indent=2)+'\n')
