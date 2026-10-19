"""Relative-error objective representation and diverse-model blending screen."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from selected_physics_interactions import augment

out=ROOT/'out/v247';out.mkdir(exist_ok=True);z=np.load(ROOT/'out/v125/fit-features.npz');y,yv=z['y'].astype(float),z['yv'].astype(float);n,nv=len(y),len(yv)
x=np.memmap(ROOT/'out/v243/all.features.f32',mode='r',dtype='<f4',shape=(n+nv,137));b=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4').astype(float);train,valid=augment(x[:n]),augment(x[n:]);bv=b[n:];b=b[:n]
r={'state':'running','fit_scope':'development only; validation representation comparison','holdout_used':False,'candidates':[]}
def record(v,p):
 v['score']=float(100*np.mean(1-np.tanh(4*abs(p-yv)/yv)));r['candidates'].append(v);(ROOT/'reports/V247-relative-and-blend.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(v),flush=True)
old=lgb.Booster(model_file=str(ROOT/'out/v216/tree8.txt')).predict(x[n:],num_threads=1)
wall=np.zeros(nv)
for i in (0,1):
 mask=(valid[:,54]>0)==bool(i);wall[mask]=lgb.Booster(model_file=str(ROOT/f'out/v244/wall-expert-{i}.txt')).predict(valid[mask],num_threads=1)
plain=lgb.Booster(model_file=str(ROOT/'out/v244/plain.txt')).predict(x[n:],num_threads=1)
for name,alternative in [('old8',old),('plain64',plain)]:
 for fraction in (.25,.5,.75):
  p=np.rint(np.maximum(0,bv+(1-fraction)*wall+fraction*alternative));np.save(out/f'blend-{name}-{fraction}.npy',p);record({'name':f'blend-{name}','fraction':fraction},p)
start=time.monotonic();model=lgb.train({'objective':'regression_l1','num_leaves':1023,'max_depth':24,'min_data_in_leaf':25,'learning_rate':.2,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019},lgb.Dataset(train,label=(y-b)/np.maximum(b,1)),num_boost_round=64);model.save_model(str(out/'relative.txt'))
for k in (8,16,32,64):
 p=np.rint(np.maximum(0,bv*(1+model.predict(valid,num_iteration=k,num_threads=1))));np.save(out/f'relative-{k}.npy',p);record({'name':'relative','trees':k,'elapsed_seconds':time.monotonic()-start},p)
r['state']='complete';r['best']=max(r['candidates'],key=lambda v:v['score']);(ROOT/'reports/V247-relative-and-blend.json').write_text(json.dumps(r,indent=2)+'\n')
