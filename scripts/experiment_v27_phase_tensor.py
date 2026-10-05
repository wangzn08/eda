"""Learn a latent min-plus route decomposition, then enforce feasible upper caps."""
import json,time,math
import numpy as np
import torch
from torch import nn
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v21_neural import graph_embedding,numerical
from experiment_v7_teacher import score

class MinPlus(nn.Module):
    def __init__(self,n):
        super().__init__();self.s=nn.Embedding(496,64);self.t=nn.Embedding(496,64)
        self.register_buffer('graph',torch.tensor(graph_embedding()))
        self.geo=nn.Sequential(nn.Linear(n+64,256),nn.SiLU(),nn.Linear(256,256),nn.SiLU(),nn.Linear(256,64))
        self.phase_source=nn.Embedding(496,8);self.phase_target=nn.Embedding(496,8)
        self.sx=nn.Parameter(torch.randn(10,8,64)*.01);self.sy=nn.Parameter(torch.randn(12,8,64)*.01)
        self.tx=nn.Parameter(torch.randn(10,8,64)*.01);self.ty=nn.Parameter(torch.randn(12,8,64)*.01)
        nn.init.normal_(self.s.weight,std=.01);nn.init.normal_(self.t.weight,std=.01)
        nn.init.zeros_(self.geo[-1].weight);nn.init.constant_(self.geo[-1].bias,2.)
    def forward(self,x,p,tau):
        geometry=torch.cat((x,self.graph[p[:,0]],self.graph[p[:,1]]),1)
        a,b=self.phase_source(p[:,0]),self.phase_target(p[:,1])
        phase=(a[:,:,None]*self.sx[p[:,2]]).sum(1)+(a[:,:,None]*self.sy[p[:,3]]).sum(1)
        phase+=(b[:,:,None]*self.tx[p[:,2]]).sum(1)+(b[:,:,None]*self.ty[p[:,3]]).sum(1)
        costs=self.s(p[:,0])+self.t(p[:,1])+self.geo(geometry)+phase
        return -tau*torch.logsumexp(-costs/tau,1)+tau*math.log(64)

def anchor(x):
    phi=lambda a:a-np.clip(a-76,0,14)
    return 12.5*np.abs(phi(x[:,2])-phi(x[:,0]))+(125/12)*np.abs(x[:,3]-x[:,1])+x[:,20]+x[:,21]

def main():
    start=time.monotonic();torch.set_num_threads(2);torch.manual_seed(20261005)
    device=torch.device('mps' if torch.backends.mps.is_available() else 'cpu');folder=ROOT/'out/v27';folder.mkdir(exist_ok=True)
    x,y,b,u=load('development');xv,yv,bv,uv=load('validation');a,va=numerical(x),numerical(xv)
    mean=a.mean(0);std=np.maximum(a.std(0),1);a=np.clip((a-mean)/std,-10,10);va=np.clip((va-mean)/std,-10,10)
    base,vbase=anchor(x),anchor(xv);m=y>0
    xx=torch.tensor(a[m],device=device);pp=torch.tensor(np.column_stack((x[m,10:12],x[m,35]%10,x[m,36]%12)),dtype=torch.long,device=device)
    yy=torch.tensor((y[m]-base[m])/100,dtype=torch.float32,device=device);w=1/y[m];w/=w.mean();ww=torch.tensor(w,dtype=torch.float32,device=device)
    vx=torch.tensor(va,device=device);vp=torch.tensor(np.column_stack((xv[:,10:12],xv[:,35]%10,xv[:,36]%12)),dtype=torch.long,device=device)
    model=MinPlus(xx.shape[1]).to(device);opt=torch.optim.AdamW(model.parameters(),lr=.0015,weight_decay=1e-5)
    prior=np.load(ROOT/'out/v19/validation-1536.npy');results=[];np.savez(folder/'normalization.npz',mean=mean,std=std)
    for epoch in range(1,161):
        tau=.03+.47*(1+math.cos(np.pi*epoch/160))/2;model.train()
        for idx in torch.randperm(len(xx),device=device).split(4096):
            opt.zero_grad(set_to_none=True);loss=(torch.abs(model(xx[idx],pp[idx],tau)-yy[idx])*ww[idx]).mean();loss.backward();opt.step()
        for g in opt.param_groups:g['lr']=.0001+.0014*(1+math.cos(np.pi*epoch/160))/2
        if epoch%8==0 or epoch==1:
            model.eval()
            with torch.no_grad():corr=torch.cat([model(vx[i:i+8192],vp[i:i+8192],tau).cpu() for i in range(0,len(vx),8192)]).numpy()
            pred=np.minimum(np.rint(np.maximum(0,vbase+100*corr)),uv);path=folder/f'minplus-{epoch}.pt'
            torch.save({'state':{k:v.detach().cpu() for k,v in model.state_dict().items()},'tau':tau},path)
            for weight in (0.,.25,.5,.75):
                final=np.minimum(np.rint((1-weight)*pred+weight*prior),uv)
                item={'epoch':epoch,'tau':tau,'v19_weight':weight,'validation_score':score(yv,final),'model':str(path.relative_to(ROOT)),'model_bytes':path.stat().st_size};results.append(item)
                np.save(folder/f'validation-{epoch}-{weight}.npy',final)
            print(json.dumps({'epoch':epoch,'standalone_score':score(yv,pred),'best_so_far':max(r['validation_score'] for r in results),'elapsed':time.monotonic()-start}),flush=True)
            (ROOT/'reports/V27-minplus-neural.json').write_text(json.dumps({'fit_split':'development','holdout_used':False,'device':str(device),
                'architecture':'Endpoint-phase tensor-factorized latent route costs: port factors interact with horizontal mod10/vertical mod12 residue factors; shared geometry; soft minimum; not path witnesses.',
                'baseline':score(yv,prior),'candidates':results,'best':max(results,key=lambda r:r['validation_score']),'elapsed_seconds':time.monotonic()-start},indent=2)+'\n')

if __name__=='__main__':main()
