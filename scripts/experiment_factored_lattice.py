"""KFL-inspired interpolated route residuals; no global monotonicity assumed."""
import json,time,numpy as np,torch
from torch import nn
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v133';out.mkdir(exist_ok=True);start=time.monotonic();torch.set_num_threads(1);device='mps' if torch.backends.mps.is_available() else 'cpu'
# Six numeric intrinsic features; categorical port identities are not interpolated.
cols=[103,104,111,121,118,119];raw=z['a'][:,cols];low=np.quantile(raw,.01,axis=0);high=np.maximum(np.quantile(raw,.99,axis=0),low+1);np.savez(out/'normalization.npz',low=low,high=high,cols=cols)
def data(a):
 x=np.clip((a[:,cols]-low)/(high-low)*7,0,7).astype(np.float32);s=a[:,99].astype(np.int64)+1;t=a[:,100].astype(np.int64)+1;g=(a[:,107].astype(np.int64)*4+(a[:,101]<0)*2+(a[:,102]<0))
 assert s.min()>=0 and s.max()<161 and t.min()>=0 and t.max()<161 and g.min()>=0 and g.max()<32
 return tuple(torch.tensor(v,device=device) for v in (x,s,t,g))
a=data(z['a']);v=data(z['av']);target=torch.tensor((z['y']-z['b'])/100,dtype=torch.float32,device=device);gold=torch.tensor(z['y'],dtype=torch.float32,device=device);base=torch.tensor(z['b'],dtype=torch.float32,device=device)
class Lattice(nn.Module):
 def __init__(self,rank):
  super().__init__();self.w=nn.Parameter(torch.ones(32,rank,6,8)+torch.randn(32,rank,6,8)*.01);self.s=nn.Parameter(torch.ones(161,rank)+torch.randn(161,rank)*.01);self.t=nn.Parameter(torch.ones(161,rank)+torch.randn(161,rank)*.01);self.scale=nn.Parameter(torch.tensor([.01*(-1)**i for i in range(rank)]).expand(32,-1).clone());self.bias=nn.Parameter(torch.zeros(32))
 def forward(self,x,s,t,g):
  lo=x.long().clamp(0,6);alpha=x-lo;values=self.w[g];i=lo[:,None,:,None].expand(-1,values.shape[1],-1,1);left=values.gather(3,i).squeeze(3);right=values.gather(3,i+1).squeeze(3);f=(left+(right-left)*alpha[:,None,:]).prod(2)*self.s[s]*self.t[t];return self.bias[g]+(f*self.scale[g]).sum(1)
report={'state':'running','fit_split':'development','holdout_used':False,'device':device,'reference':'Morioka et al. ICLR2021 KFL; adapted expression, not full paper replication','monotonicity_enforced':False,'scope':'Python prototype, end-to-end deployment and throughput unverified','candidates':[]}
for rank in (2,4,8):
 torch.manual_seed(20261007);m=Lattice(rank).to(device);opt=torch.optim.AdamW(m.parameters(),lr=.006,weight_decay=.0001)
 for epoch in range(1,25):
  for ix in torch.randperm(len(target),device=device).split(8192):
   opt.zero_grad(set_to_none=True);pred=base[ix]+100*m(*(q[ix] for q in a));loss=torch.tanh(4*(pred-gold[ix]).abs()/gold[ix].clamp(min=1)).mean();loss.backward();opt.step()
  if epoch%8==0:
   with torch.no_grad():r=torch.cat([m(*(q[i:i+8192] for q in v)).cpu() for i in range(0,len(v[0]),8192)]).numpy()
   p=np.rint(np.maximum(0,z['bv']+100*r));np.save(out/f'rank{rank}-epoch{epoch}.npy',p);torch.save({k:q.detach().cpu() for k,q in m.state_dict().items()},out/f'rank{rank}-epoch{epoch}.pt');item={'rank':rank,'epoch':epoch,'score':score(z['yv'],p),'parameter_float32_bytes':sum(q.numel()*4 for q in m.parameters()),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V133-factored-lattice.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V133-factored-lattice.json').write_text(json.dumps(report,indent=2)+'\n')
