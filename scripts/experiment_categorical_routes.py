"""Test categorical route topology rather than ordinal port identifiers."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from experiment_v7_teacher import score
out=ROOT/'out/v121';out.mkdir(exist_ok=True);z=np.load(ROOT/'out/v117/fit-features.npz');a,av,y,yv,b,bv=[z[k] for k in ('a','av','y','yv','b','bv')];route=np.load(ROOT/'out/v117/route-data.npz');r,rv=route['development'],route['validation'];start=time.monotonic()
# Preserve topology as categories: core identities, core pair, family/lane pair.
extra=lambda t:np.column_stack((t[:,0],t[:,1],t[:,0]*160+t[:,1],np.floor_divide(t[:,0],8)*20+np.floor_divide(t[:,1],8),(t[:,0]-t[:,1])%8,t[:,8])).astype(np.float32)
aug=np.column_stack((a,extra(r)));augv=np.column_stack((av,extra(rv)));cat=[9,10]+list(range(a.shape[1],aug.shape[1]))
report={'state':'running','fit_split':'development','holdout_used':False,'scope':'Python categorical challenger, no accepted runtime or serialized size','candidates':[]}
for leaves in (63,255):
 ds=lgb.Dataset(aug,label=y-b,weight=1000/np.maximum(y,1),categorical_feature=cat)
 m=lgb.train({'objective':'regression_l1','learning_rate':.07,'num_leaves':leaves,'min_data_in_leaf':30,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007,'cat_smooth':10,'cat_l2':5,'max_cat_threshold':64},ds,num_boost_round=256)
 m.save_model(str(out/f'categorical-{leaves}.txt'))
 for trees in (32,64,128,256):
  p=np.rint(np.maximum(0,bv+m.predict(augv,num_iteration=trees,num_threads=1)));np.save(out/f'l{leaves}-t{trees}.npy',p);item={'leaves':leaves,'trees':trees,'score':score(yv,p),'elapsed':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True)
 (ROOT/'reports/V121-categorical-route-models.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V121-categorical-route-models.json').write_text(json.dumps(report,indent=2)+'\n')
