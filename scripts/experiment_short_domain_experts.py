"""Fewer expert paths with faster boosting convergence; development fit only."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from selected_physics_interactions import augment

out=ROOT/'out/v252';out.mkdir(exist_ok=True);z=np.load(ROOT/'out/v125/fit-features.npz');y,yv=z['y'].astype(float),z['yv'].astype(float);n,nv=len(y),len(yv)
x=np.memmap(ROOT/'out/v243/all.features.f32',mode='r',dtype='<f4',shape=(n+nv,137));base=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4').astype(float);b,bv=base[:n],base[n:]
columns=list(range(69))+list(range(125,137));gate=lgb.Booster(model_file=str(ROOT/'out/v248/geometry-255.txt'));need=gate.predict(x[n:,columns],num_threads=1)>=.5
ids=x[:n,54]>0;idsv=x[n:,54]>0
report={'state':'running','fit_scope':'development only, full validation comparison','holdout_used':False,'gate':'out/v248/geometry-255.txt','gate_threshold':.5,'candidates':[]}
def record(item,p):
 item['score']=float(100*np.mean(1-np.tanh(4*abs(p-yv)/yv)));report['candidates'].append(item);(ROOT/'reports/V252-short-domain-experts.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(item),flush=True)
for name,leaves,rate,enriched in [('physics1023-r35',1023,.35,True),('physics1023-r50',1023,.5,True),('physics511-r35',511,.35,True),('plain1023-r35',1023,.35,False)]:
 start=time.monotonic();train,valid=(augment(x[:n]),augment(x[n:])) if enriched else (np.asarray(x[:n]),np.asarray(x[n:]))
 models=[]
 for domain in (0,1):
  selected=ids==bool(domain);ds=lgb.Dataset(train[selected],label=(y-b)[selected],weight=1000/np.maximum(y[selected],1));model=lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':24,'min_data_in_leaf':25,'learning_rate':rate,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019},ds,num_boost_round=16);model.save_model(str(out/f'{name}-{domain}.txt'));models.append(model)
 for k in (8,12,16):
  correction=np.zeros(nv)
  for domain,model in enumerate(models):
   selected=idsv==bool(domain);correction[selected]=model.predict(valid[selected],num_iteration=k,num_threads=1)
  full=np.rint(np.maximum(0,bv+correction))
  for selective in (False,True):
   prediction=np.where(need,full,bv) if selective else full;path=f'{name}-{k}'+('-gated' if selective else '')+'.npy';np.save(out/path,prediction);record({'name':name,'trees_per_request':k,'total_trees':2*k,'features':train.shape[1],'selective':selective,'prediction':f'out/v252/{path}','elapsed_seconds':time.monotonic()-start},prediction)
report['state']='complete';report['best']=max(report['candidates'],key=lambda v:v['score']);(ROOT/'reports/V252-short-domain-experts.json').write_text(json.dumps(report,indent=2)+'\n')
