"""Shared branch corrections followed by min-cost selection, development-only fit."""
import json,time,math
import numpy as np,torch
from torch import nn
from architecture import ROOT
from experiment_v7_teacher import score
torch.set_num_threads(1);device='mps' if torch.backends.mps.is_available() else 'cpu'
z=np.load(ROOT/'out/v125/fit-features.npz');raw=np.loadtxt(ROOT/'out/v144/branches.csv',delimiter=',',dtype=np.float32);assert raw.shape==(850758,70)
out=ROOT/'out/v165';out.mkdir(exist_ok=True);n=len(z['y']);cols=[i for i in list(range(27))+list(range(71,99))+list(range(121,133)) if i not in (80,94)]
branch=raw[:,2:].reshape(-1,4,17);mask=branch[:,:,0]>=0
own=branch.copy();own[:,:,0]-=raw[:,0,None];own[:,:,1:4]=0
ownmean=own[:n][mask[:n]].mean(axis=0);ownstd=np.maximum(own[:n][mask[:n]].std(axis=0),1)
lo=np.quantile(z['a'][:,cols],.01,axis=0);hi=np.maximum(np.quantile(z['a'][:,cols],.99,axis=0),lo+1)
np.savez(out/'normalization.npz',cols=cols,lo=lo,hi=hi,ownmean=ownmean,ownstd=ownstd)
def build(a,start,end):
 x=np.clip((a[:,cols]-lo)/(hi-lo),-1,2).astype(np.float32)
 p=a[:,[80,94]].astype(np.int64);b=branch[start:end];c=np.column_stack((b[:,:,1]+1,b[:,:,2]+1,b[:,:,3]+1)).reshape(len(a),3,4).transpose(0,2,1).astype(np.int64)
 values=(np.clip((own[start:end]-ownmean)/ownstd,-8,8)).astype(np.float32)
 return tuple(torch.tensor(q,device=device) for q in (x,p,c,values,b[:,:,0],mask[start:end],raw[start:end,0]))
train=build(z['a'],0,n);valid=build(z['av'],n,len(raw));gold=torch.tensor(z['y'],dtype=torch.float32,device=device)
class Net(nn.Module):
 def __init__(self):
  super().__init__();self.endpoint=nn.ModuleList([nn.Embedding(496,16) for _ in range(2)]);self.core=nn.ModuleList([nn.Embedding(161,16) for _ in range(2)]);self.kind=nn.Embedding(8,8)
  self.layers=nn.Sequential(nn.Linear(len(cols)+17+32+32+16+8,128),nn.LeakyReLU(.1),nn.Linear(128,32),nn.LeakyReLU(.1),nn.Linear(32,1));nn.init.zeros_(self.layers[-1].weight);nn.init.zeros_(self.layers[-1].bias)
 def forward(self,x,p,c,v,delay,mask,base,temperature=0):
  e=[emb(p[:,k])[:,None,:].expand(-1,4,-1) for k,emb in enumerate(self.endpoint)];h=[emb(c[:,:,k].clamp(0,160)) for k,emb in enumerate(self.core)]
  delta=20*self.layers(torch.cat((x[:,None,:].expand(-1,4,-1),v,*e,*h,h[0]*h[1],self.kind(c[:,:,2].clamp(0,7))),2)).squeeze(2)
  costs=torch.where(mask,delay+delta,torch.full_like(delay,1e7))
  result=-temperature*torch.logsumexp(-costs/temperature,dim=1) if temperature else costs.min(dim=1).values
  original_min=torch.where(mask,delay,torch.full_like(delay,1e7)).min(dim=1).values
  return torch.where(mask.any(dim=1)&(base>=original_min),result,base)
r={'state':'running','fit_split':'development','holdout_used':False,'architecture':'Shared endpoint/core-conditioned correction for four source branches, then min-cost selection','scope':'MPS accuracy prototype; deployment cost and compression pending','candidates':[]};start=time.monotonic()
for policy in ['hard','annealed']:
 torch.manual_seed(20261007);model=Net().to(device);opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.001)
 for epoch in range(1,65):
  for group in opt.param_groups:group['lr']=.00005+.00095*(1+math.cos(math.pi*epoch/64))/2
  for ix in torch.randperm(n,device=device).split(4096):
   opt.zero_grad(set_to_none=True);pred=model(*(q[ix] for q in train),temperature=max(.05,2*(1-epoch/64)) if policy=='annealed' else 0)
   loss=torch.tanh(4*(pred-gold[ix]).abs()/gold[ix].clamp(min=1)).mean();loss.backward();opt.step()
  if epoch%16==0:
   with torch.no_grad():p=torch.cat([model(*(q[i:i+4096] for q in valid)).cpu() for i in range(0,len(z['yv']),4096)]).numpy()
   p=np.rint(np.maximum(0,p));name=f'{policy}-{epoch}';np.save(out/f'{name}.npy',p);torch.save({k:v.detach().cpu() for k,v in model.state_dict().items()},out/f'{name}.pt');item={'name':name,'score':score(z['yv'],p),'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V165-min-route-network.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V165-min-route-network.json').write_text(json.dumps(r,indent=2)+'\n')
