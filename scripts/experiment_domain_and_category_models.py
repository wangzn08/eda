"""Follow up physical domain experts and categorical port representation."""
import json, time
import lightgbm as lgb
import numpy as np
from architecture import ROOT
from selected_physics_interactions import augment

out=ROOT/'out/v245';out.mkdir(exist_ok=True)
z=np.load(ROOT/'out/v125/fit-features.npz');y,yv=z['y'].astype(float),z['yv'].astype(float);n,nv=len(y),len(yv)
x=np.memmap(ROOT/'out/v243/all.features.f32',mode='r',dtype='<f4',shape=(n+nv,137));base=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4').astype(float);b,bv=base[:n],base[n:]
a,av=augment(x[:n]),augment(x[n:]);params={'objective':'regression_l1','max_depth':24,'min_data_in_leaf':25,'learning_rate':.2,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019}
report={'state':'running','fit_scope':'development only; native V242 features; validation only for comparison','holdout_used':False,'candidates':[]}
def record(item,p):
 item.update(score=float(100*np.mean(1-np.tanh(4*abs(p-yv)/yv))),exact_fraction=float(np.mean(p==yv)));report['candidates'].append(item);(ROOT/'reports/V245-domain-and-category-models.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(item),flush=True)
for scheme,leaves,rounds in [('wall-wide',1023,32),('four-regions',511,32)]:
 start=time.monotonic();ids=(x[:n,54]>0).astype(int);idsv=(x[n:,54]>0).astype(int)
 if scheme=='four-regions':ids=ids*2+(x[:n,22]<96);idsv=idsv*2+(x[n:,22]<96)
 models=[]
 for i in range(2 if scheme=='wall-wide' else 4):
  mask=ids==i;model=lgb.train({**params,'num_leaves':leaves},lgb.Dataset(a[mask],label=(y-b)[mask],weight=1000/np.maximum(y[mask],1)),num_boost_round=rounds);model.save_model(str(out/f'{scheme}-{i}.txt'));models.append(model)
 for k in (8,16,32):
  correction=np.zeros(nv)
  for i,m in enumerate(models):
   mask=idsv==i;correction[mask]=m.predict(av[mask],num_iteration=k,num_threads=1)
  p=np.rint(np.maximum(0,bv+correction));np.save(out/f'{scheme}-{k}.npy',p);record({'name':scheme,'trees_per_request':k,'total_trees':k*len(models),'leaves':leaves,'elapsed_seconds':time.monotonic()-start},p)
start=time.monotonic()
cat=[7,8,9,10,13,14,15,16,17,18]
model=lgb.train({**params,'num_leaves':1023,'cat_smooth':20,'cat_l2':20},lgb.Dataset(a,label=y-b,weight=1000/np.maximum(y,1),categorical_feature=cat),num_boost_round=64);model.save_model(str(out/'categorical.txt'))
for k in (8,16,32,64):
 p=np.rint(np.maximum(0,bv+model.predict(av,num_iteration=k,num_threads=1)));np.save(out/f'categorical-{k}.npy',p);record({'name':'categorical','trees':k,'leaves':1023,'elapsed_seconds':time.monotonic()-start},p)
report['state']='complete';report['best']=max(report['candidates'],key=lambda i:i['score']);(ROOT/'reports/V245-domain-and-category-models.json').write_text(json.dumps(report,indent=2)+'\n')
