"""Second-order sparse route FM, dev-only official-score fitting (not paper solver)."""
import json,time,math
import numpy as np,torch
from torch import nn
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v123';out.mkdir(exist_ok=True);torch.set_num_threads(1);device='mps' if torch.backends.mps.is_available() else 'cpu';z=np.load(ROOT/'out/v117/route-data.npz');x,y,_,_=load('development');v,yv,_,_=load('validation');b,bv=z['development_base'],z['validation_base'];r,rv=z['development'].astype(np.int64),z['validation'].astype(np.int64)
def modes(x,t,joint):
 s=np.maximum(t[:,0],0);p=np.maximum(t[:,1],0);phase=(t[:,6]%10)*12+t[:,7]%12;cols=[x[:,10].astype(int),x[:,11].astype(int),s,p,phase,(t[:,2]>0)*2+(t[:,3]>0),np.minimum(t[:,4],11),np.minimum(t[:,5],45),np.minimum(t[:,8],4),x[:,0].astype(int),x[:,2].astype(int),x[:,1].astype(int)%100,x[:,3].astype(int)%100,np.minimum(t[:,12],255)];dims=[496,496,160,160,120,4,12,46,5,120,120,100,100,256]
 if joint:cols += [s*120+phase,p*120+phase,s*160+p];dims +=[19200,19200,25600]
 offsets=np.r_[0,np.cumsum(dims)[:-1]];return np.column_stack(cols).astype(np.int64)+offsets,int(sum(dims))
class FM(nn.Module):
 def __init__(self,n,k):
  super().__init__();self.factors=nn.Embedding(n,k);self.linear=nn.Embedding(n,1);self.bias=nn.Parameter(torch.zeros(()));nn.init.normal_(self.factors.weight,std=.01);nn.init.zeros_(self.linear.weight)
 def forward(self,t):
  v=self.factors(t);return self.bias+self.linear(t).sum((1,2))+.5*(v.sum(1).square()-v.square().sum(1)).sum(1)
report={'state':'running','fit_split':'development','holdout_used':False,'prediction_cache':False,'device':device,'reference':'Blondel et al.2016 arxiv1607.08810; second-order ANOVA/FM equation, AdamW rather than paper coordinate descent','candidates':[]};start=time.monotonic()
for joint,rank in [(False,8),(True,8)]:
 a,n=modes(x,r,joint);av,_=modes(v,rv,joint);aa=torch.tensor(a,device=device);vv=torch.tensor(av,device=device);label=torch.tensor((y-b)/100,dtype=torch.float32,device=device);weight=torch.tensor(400/np.maximum(y,1),dtype=torch.float32,device=device);torch.manual_seed(20261007);m=FM(n,rank).to(device);opt=torch.optim.AdamW(m.parameters(),lr=.003,weight_decay=.01)
 for epoch in range(1,25):
  m.train()
  for idx in torch.randperm(len(y),device=device).split(8192):
   opt.zero_grad(set_to_none=True);e=m(aa[idx])-label[idx];loss=torch.tanh(torch.sqrt(e.square()+1e-8)*weight[idx]).mean();loss.backward();opt.step()
  for group in opt.param_groups:group['lr']=.0003+.0027*(1+math.cos(math.pi*epoch/24))/2
  if epoch%4==0:
   m.eval()
   with torch.no_grad():delta=torch.cat([m(vv[i:i+8192]).cpu() for i in range(0,len(yv),8192)]).numpy()
   p=np.rint(np.maximum(0,bv+100*delta));name=f'joint{int(joint)}-r{rank}-e{epoch}';np.save(out/f'{name}.npy',p);torch.save({'state':{k:w.detach().cpu() for k,w in m.state_dict().items()},'joint':joint,'rank':rank,'count':n},out/f'{name}.pt');item={'name':name,'score':score(yv,p),'float16_parameter_bytes':sum(w.numel()*2 for w in m.parameters()),'elapsed':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V123-route-factorization.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V123-route-factorization.json').write_text(json.dumps(report,indent=2)+'\n')
