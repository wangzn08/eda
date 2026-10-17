"""Residual architecture: learned port interactions plus all intrinsic diagnostics.
Development labels only. Accuracy screening precedes compact deployment design.
"""
import json,time,math
import numpy as np
import torch
from torch import nn
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v142';out.mkdir(exist_ok=True);torch.set_num_threads(1);device='mps' if torch.backends.mps.is_available() else 'cpu';start=time.monotonic();cols=[i for i in range(133) if i not in (80,94,99,100)]
a=z['a'];lo=np.quantile(a[:,cols],.01,axis=0);hi=np.maximum(np.quantile(a[:,cols],.99,axis=0),lo+1);np.savez(out/'normalization.npz',lo=lo,hi=hi,cols=cols)
def build(a):
 x=np.clip((a[:,cols]-lo)/(hi-lo),-1,2).astype(np.float32);p=np.column_stack((a[:,80],a[:,94],a[:,99]+1,a[:,100]+1)).astype(np.int64);g=a[:,107].astype(np.int64)*4+(a[:,101]<0)*2+(a[:,102]<0);return tuple(torch.tensor(v,device=device) for v in (x,p,g))
train=build(a);valid=build(z['av']);gold=torch.tensor(z['y'],dtype=torch.float32,device=device);base=torch.tensor(z['b'],dtype=torch.float32,device=device)
class Net(nn.Module):
 def __init__(self,width):
  super().__init__();self.embedding=nn.ModuleList([nn.Embedding(n,32) for n in (496,496,161,161)]);self.route=nn.Embedding(32,16);self.layers=nn.Sequential(nn.Linear(len(cols)+128+64+16,width),nn.ReLU(),nn.Linear(width,width//2),nn.ReLU(),nn.Linear(width//2,64),nn.ReLU(),nn.Linear(64,1));nn.init.zeros_(self.layers[-1].weight);nn.init.zeros_(self.layers[-1].bias)
 def forward(self,x,p,g):
  e=[q(p[:,i]) for i,q in enumerate(self.embedding)];return self.layers(torch.cat([x,*e,e[0]*e[1],e[2]*e[3],self.route(g)],1)).squeeze(1)
r={'state':'running','fit_split':'development','holdout_used':False,'scope':'full-validation accuracy prototype; C++ deployment and time budget pending','reference':'Revisiting Deep Learning Models for Tabular Data2021 and factorization-machine port interactions; no claim of a new neural primitive','candidates':[]}
for width in (128,256):
 torch.manual_seed(20261007);m=Net(width).to(device);opt=torch.optim.AdamW(m.parameters(),lr=.001,weight_decay=.002)
 for epoch in range(1,129):
  for group in opt.param_groups:group['lr']=.00005+.00095*(1+math.cos(math.pi*epoch/128))/2
  for ix in torch.randperm(len(gold),device=device).split(4096):
   opt.zero_grad(set_to_none=True);pred=base[ix]+100*m(*(q[ix] for q in train));loss=torch.tanh(4*(pred-gold[ix]).abs()/gold[ix].clamp(min=1)).mean();loss.backward();opt.step()
  if epoch%16==0:
   with torch.no_grad():correction=torch.cat([m(*(q[i:i+4096] for q in valid)).cpu() for i in range(0,len(valid[0]),4096)]).numpy()
   p=np.rint(np.maximum(0,z['bv']+100*correction));name=f'width{width}-epoch{epoch}';np.save(out/(name+'.npy'),p);torch.save({k:v.detach().cpu() for k,v in m.state_dict().items()},out/(name+'.pt'));item={'width':width,'epoch':epoch,'score':score(z['yv'],p),'parameter_float32_bytes':sum(q.numel()*4 for q in m.parameters()),'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V142-port-interaction-network.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V142-port-interaction-network.json').write_text(json.dumps(r,indent=2)+'\n')
