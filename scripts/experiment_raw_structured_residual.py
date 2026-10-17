"""V101: remove in-sample learned-baseline dependence; raw architecture residual fit."""
import csv,json,time
import numpy as np
import torch
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
from structured_residual_models import modes,TrainTensor,MultiScale,hashmodes

def read(name):
 with (ROOT/'out/evaluation'/name).open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],np.float64)
torch.set_num_threads(2);torch.manual_seed(20261007);start=time.monotonic();out=ROOT/'out/v101';out.mkdir(exist_ok=True)
x,y,_,_=load('development');v,yv,_,_=load('validation');b=read('development.v93-joint.csv');bv=read('validation.v93-base.csv');retained=np.load(ROOT/'out/v99/retained-v93-64.npy');mask=y>0
w=torch.tensor((1000/np.maximum(y[mask],100)).astype(np.float32));w/=w.mean();target=torch.tensor(((y[mask]-b[mask])/100).astype(np.float32))
report={'fit_split':'development','holdout_used':False,'scope':'Raw architecture residual, fixed 32-epoch schedule, Python only','candidates':[]}
for name,m,z,zv in [('tensor-r8',TrainTensor(8),modes(x),modes(v)),('tensor-r16',TrainTensor(16),modes(x),modes(v)),('multiscale-hash',MultiScale(),hashmodes(x),hashmodes(v))]:
 z=torch.tensor(z[mask]);zv=torch.tensor(zv);opt=torch.optim.Adam(m.parameters(),lr=.003)
 for epoch in range(1,33):
  m.train()
  for ids in torch.randperm(len(z)).split(4096):
   delta=m(z[ids]);loss=(w[ids]*torch.nn.functional.smooth_l1_loss(delta,target[ids],beta=.05,reduction='none')).mean();opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
  if epoch in (8,16,32):
   m.eval()
   with torch.no_grad():d=torch.cat([m(t) for t in zv.split(8192)]).numpy()*100
   p=np.rint(np.maximum(0,bv+d));np.save(out/f'{name}-e{epoch}.npy',p);torch.save(m.state_dict(),out/f'{name}-e{epoch}.pt')
   report['candidates'].append({'name':name,'epoch':epoch,'score':score(yv,p),'correction_abs_mean_ps':float(np.mean(abs(d))),'parameter_bytes':sum(t.numel()*t.element_size() for t in m.parameters()),'elapsed_seconds':time.monotonic()-start});print(json.dumps(report['candidates'][-1]),flush=True)
   (ROOT/'reports/V101-raw-structured-residual.json').write_text(json.dumps(report,indent=2)+'\n')
