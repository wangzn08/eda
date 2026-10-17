"""Three-action score-sensitive residual gate with separately supervised experts.
Actions are preserve, increase, decrease; fitted exclusively on development.
"""
import json,time,math
import numpy as np,torch
from torch import nn
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v159';out.mkdir(exist_ok=True);torch.set_num_threads(1);device='mps' if torch.backends.mps.is_available() else 'cpu';start=time.monotonic();cols=json.loads((out/'feature-cols.json').read_text());a=z['a'];lo=np.quantile(a[:,cols],.01,axis=0);hi=np.maximum(np.quantile(a[:,cols],.99,axis=0),lo+1);np.savez(out/'normalization.npz',lo=lo,hi=hi,cols=cols)
def build(a):
 x=np.clip((a[:,cols]-lo)/(hi-lo),-1,2).astype(np.float32);p=np.column_stack((a[:,80],a[:,94],a[:,99]+1,a[:,100]+1)).astype(np.int64);return tuple(torch.tensor(v,device=device) for v in (x,p))
train=build(a);valid=build(z['av']);gold=torch.tensor(z['y'],dtype=torch.float32,device=device);base=torch.tensor(z['b'],dtype=torch.float32,device=device);err=gold-base;classes=(torch.sign(err)+1).long()
class Net(nn.Module):
 def __init__(self,width):
  super().__init__();self.embedding=nn.ModuleList([nn.Embedding(n,8) for n in (496,496,161,161)]);self.body=nn.Sequential(nn.Linear(64,width),nn.LeakyReLU(.1),nn.Linear(width,32),nn.LeakyReLU(.1));self.gate=nn.Linear(32,3);self.expert=nn.Linear(32,2);nn.init.zeros_(self.expert.weight);nn.init.constant_(self.expert.bias,-2)
 def forward(self,x,p):
  h=self.body(torch.cat([x,*[e(p[:,i]) for i,e in enumerate(self.embedding)]],1));return self.gate(h),10*torch.nn.functional.softplus(self.expert(h))
r={'state':'running','fit_split':'development','holdout_used':False,'scope':'Lightweight score-sensitive three-action prototype; not a native timing result','reference':'TabularDL2021 for tabular embeddings; adapted cost-sensitive gate and positive/negative residual experts','features':cols,'candidates':[]}
for width in (64,128):
 torch.manual_seed(20261007);m=Net(width).to(device);opt=torch.optim.AdamW(m.parameters(),lr=.0015,weight_decay=.001)
 for epoch in range(1,81):
  for group in opt.param_groups:group['lr']=.0001+.0014*(1+math.cos(math.pi*epoch/80))/2
  for ix in torch.randperm(len(gold),device=device).split(4096):
   opt.zero_grad(set_to_none=True);logits,mag=m(*(q[ix] for q in train));actions=torch.stack((-mag[:,0],torch.zeros_like(mag[:,0]),mag[:,1]),1);cost=torch.tanh(4*(base[ix,None]+actions.detach()-gold[ix,None]).abs()/gold[ix,None].clamp(min=1));gate_loss=(torch.softmax(logits,1)*cost).sum(1).mean();nonzero=classes[ix]!=1;expert_index=(classes[ix]==2).long();chosen=mag.gather(1,expert_index[:,None]).squeeze(1);reg=torch.tanh(4*(chosen-err[ix].abs()).abs()/gold[ix].clamp(min=1));expert_loss=reg[nonzero].mean();loss=gate_loss+expert_loss+.001*torch.nn.functional.cross_entropy(logits,classes[ix]);loss.backward();opt.step()
  if epoch%16==0:
   with torch.no_grad():chunks=[m(*(q[i:i+4096] for q in valid)) for i in range(0,len(valid[0]),4096)];logits=torch.cat([q[0].cpu() for q in chunks]);mag=torch.cat([q[1].cpu() for q in chunks]).numpy();prob=torch.softmax(logits,1).numpy()
   actions=np.column_stack((-mag[:,0],np.zeros(len(mag)),mag[:,1]));choice=prob.argmax(1);row=np.arange(len(choice));policies={'hard':actions[row,choice],'mean':(prob*actions).sum(1),'conf55':np.where(prob[row,choice]>=.55,actions[row,choice],0),'conf65':np.where(prob[row,choice]>=.65,actions[row,choice],0)}
   for policy,correction in policies.items():
    pred=np.rint(np.maximum(0,z['bv']+correction));name=f'width{width}-epoch{epoch}-{policy}';np.save(out/(name+'.npy'),pred);item={'width':width,'epoch':epoch,'policy':policy,'score':score(z['yv'],pred),'parameter_float32_bytes':sum(q.numel()*4 for q in m.parameters()),'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True)
   torch.save({k:v.detach().cpu() for k,v in m.state_dict().items()},out/f'width{width}-epoch{epoch}.pt');(ROOT/'reports/V159-score-gated-experts.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V159-score-gated-experts.json').write_text(json.dumps(r,indent=2)+'\n')
