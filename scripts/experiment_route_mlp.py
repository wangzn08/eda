"""Small piecewise-linear route residuals; labels only from development."""
import json,time,numpy as np,torch,math
from torch import nn
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v139';out.mkdir(exist_ok=True);torch.set_num_threads(1);device='mps' if torch.backends.mps.is_available() else 'cpu';start=time.monotonic()
cols=[103,104,105,106,108,111,113,121,118,119,109,110,85,87,77,91];a=z['a'];lo=np.quantile(a[:,cols],.01,axis=0);hi=np.maximum(np.quantile(a[:,cols],.99,axis=0),lo+1);np.savez(out/'normalization.npz',lo=lo,hi=hi,cols=cols)
def build(a):
 x=np.clip((a[:,cols]-lo)/(hi-lo),-1,2).astype(np.float32);p=np.column_stack((a[:,80],a[:,94],a[:,99]+1,a[:,100]+1)).astype(np.int64);g=(a[:,107].astype(np.int64)*4+(a[:,101]<0)*2+(a[:,102]<0));return tuple(torch.tensor(v,device=device) for v in (x,p,g))
train=build(a);valid=build(z['av']);gold=torch.tensor(z['y'],dtype=torch.float32,device=device);base=torch.tensor(z['b'],dtype=torch.float32,device=device)
class Net(nn.Module):
 def __init__(self,gated):
  super().__init__();self.gated=gated;self.embedding=nn.ModuleList([nn.Embedding(n,8) for n in (496,496,161,161)])
  if gated:
   self.w1=nn.Parameter(torch.randn(32,48,32)*.04);self.b1=nn.Parameter(torch.zeros(32,32));self.w2=nn.Parameter(torch.randn(32,32,16)*.06);self.b2=nn.Parameter(torch.zeros(32,16));self.w3=nn.Parameter(torch.zeros(32,16));self.b3=nn.Parameter(torch.zeros(32))
  else:self.layers=nn.Sequential(nn.Linear(48,64),nn.ReLU(),nn.Linear(64,32),nn.ReLU(),nn.Linear(32,1));nn.init.zeros_(self.layers[-1].weight);nn.init.zeros_(self.layers[-1].bias)
 def forward(self,x,p,g):
  x=torch.cat([x,*[e(p[:,i]) for i,e in enumerate(self.embedding)]],1)
  if not self.gated:return self.layers(x).squeeze(1)
  x=torch.relu(torch.bmm(x[:,None,:],self.w1[g]).squeeze(1)+self.b1[g]);x=torch.relu(torch.bmm(x[:,None,:],self.w2[g]).squeeze(1)+self.b2[g]);return (x*self.w3[g]).sum(1)+self.b3[g]
report={'state':'running','fit_split':'development','holdout_used':False,'scope':'New small residual-head prototype, not deployed or timed end-to-end','reference':'Revisiting Deep Learning Models for Tabular Data2021; adapted route features/grouped ReLU heads','candidates':[]}
for gated in (False,True):
 torch.manual_seed(20261007);m=Net(gated).to(device);opt=torch.optim.AdamW(m.parameters(),lr=.002,weight_decay=.001)
 for epoch in range(1,65):
  for group in opt.param_groups:group['lr']=.0001+.0019*(1+math.cos(math.pi*epoch/64))/2
  for ix in torch.randperm(len(gold),device=device).split(8192):
   opt.zero_grad(set_to_none=True);p=base[ix]+100*m(*(q[ix] for q in train));loss=torch.tanh(4*(p-gold[ix]).abs()/gold[ix].clamp(min=1)).mean();loss.backward();opt.step()
  if epoch%16==0:
   with torch.no_grad():r=torch.cat([m(*(q[i:i+8192] for q in valid)).cpu() for i in range(0,len(valid[0]),8192)]).numpy()
   p=np.rint(np.maximum(0,z['bv']+100*r));name=f'gated{int(gated)}-epoch{epoch}';np.save(out/(name+'.npy'),p);torch.save({k:v.detach().cpu() for k,v in m.state_dict().items()},out/(name+'.pt'));item={'gated':gated,'epoch':epoch,'score':score(z['yv'],p),'parameter_float32_bytes':sum(q.numel()*4 for q in m.parameters()),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V139-small-route-mlp.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V139-small-route-mlp.json').write_text(json.dumps(report,indent=2)+'\n')
