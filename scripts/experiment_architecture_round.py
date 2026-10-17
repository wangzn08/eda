"""V99: distinct development-fit architectures; validation only, no holdout."""
import csv,json,time,urllib.request
from pathlib import Path
import numpy as np
import torch
from torch import nn
from catboost import CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features
from experiment_v7_teacher import score

OUT=ROOT/'out/v99';OUT.mkdir(exist_ok=True)
torch.set_num_threads(2);torch.manual_seed(20261007)
report={'fit_split':'development','holdout_used':False,'scope':'Python research prototypes; no C++ throughput or submission claim','candidates':[]}
def read(name):
 with (ROOT/'out/evaluation'/name).open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],np.float64)
def boundary(x):
 cols=[]
 for cx,cy in ((x[:,0],x[:,1]),(x[:,2],x[:,3])):
  cols.extend([cx,119-cx,cy,549-cy,abs(cx-75),abs(cx-90),cy%100,49-cy%100,99-cy%100,(cy%100<50).astype(float)])
  for step in (2,4,8,16):
   cols.extend([np.minimum(cx,step),np.minimum(119-cx,step),np.minimum(cy,step),np.minimum(549-cy,step)])
 return np.column_stack(cols).astype(np.float32)
from structured_residual_models import modes,TrainTensor,MultiScale,hashmodes
def record(name,p,model=None,extra=None):
 item={'name':name,'score':score(yv,p),'mean_abs_error_ps':float(np.mean(abs(yv-p))),'elapsed_seconds':time.monotonic()-start}
 if model is not None:item['parameter_bytes']=sum(v.numel()*v.element_size() for v in model.parameters())
 if extra:item.update(extra)
 np.save(OUT/(name+'.npy'),p);report['candidates'].append(item);(ROOT/'reports/V99-architecture-round.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(item),flush=True)
start=time.monotonic();x,y,_,_=load('development');xv,yv,_,_=load('validation');raw=read('development.v93-joint.csv');rv=read('validation.v93-base.csv')
a=features(x,raw);av=features(xv,rv)
a[:,27]=x[:,1]%100;a[:,28]=x[:,3]%100;av[:,27]=xv[:,1]%100;av[:,28]=xv[:,3]%100
old=CatBoostRegressor();old.load_model(str(ROOT/'out/v93/correction.json'),format='json')
b=np.rint(np.maximum(0,raw+100*old.predict(a,ntree_end=64,thread_count=2)));bv=np.rint(np.maximum(0,rv+100*old.predict(av,ntree_end=64,thread_count=2)))
record('retained-v93-64',bv)
# Direction A: explicit physical boundary representation, retrain compact tree head.
for depth,iterations in [(8,256),(10,128)]:
 m=CatBoostRegressor(iterations=iterations,depth=depth,learning_rate=.09,loss_function='MAE',thread_count=2,random_seed=20261007,l2_leaf_reg=8,verbose=64,allow_writing_files=False)
 mask=y>0;m.fit(np.column_stack([a,boundary(x)])[mask],(y[mask]-raw[mask])/100,sample_weight=1/np.maximum(y[mask],1))
 m.save_model(str(OUT/f'boundary-{depth}.cbm'))
 for nt in (64,iterations):record(f'boundary-d{depth}-t{nt}',np.rint(np.maximum(0,rv+100*m.predict(np.column_stack([av,boundary(xv)]),ntree_end=nt,thread_count=2))))
# Directions B and C learn residual of the retained predictor. Fixed development schedule.
mask=(y>0)&np.isfinite(y);target=torch.tensor(((y[mask]-b[mask])/100).astype(np.float32));w=torch.tensor((1000/np.maximum(y[mask],100)).astype(np.float32));w/=w.mean()
for name,model,z,zv in [('tensor-r8',TrainTensor(8),modes(x),modes(xv)),('tensor-r16',TrainTensor(16),modes(x),modes(xv)),('multiscale-hash',MultiScale(),hashmodes(x),hashmodes(xv))]:
 z=torch.tensor(z[mask]);zv=torch.tensor(zv);optimizer=torch.optim.Adam(model.parameters(),lr=.008);best=-1
 for epoch in range(1,13):
  model.train();order=torch.randperm(len(z))
  for ids in order.split(4096):
   pred=model(z[ids]);loss=(w[ids]*torch.abs(pred-target[ids])).mean();optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);optimizer.step()
  if epoch in (4,8,12):
   model.eval()
   with torch.no_grad():delta=torch.cat([model(t) for t in zv.split(8192)]).numpy()*100
   p=np.rint(np.maximum(0,bv+delta));record(f'{name}-e{epoch}',p,model)
   torch.save(model.state_dict(),OUT/f'{name}-e{epoch}.pt')
report['elapsed_seconds']=time.monotonic()-start;(ROOT/'reports/V99-architecture-round.json').write_text(json.dumps(report,indent=2)+'\n')
