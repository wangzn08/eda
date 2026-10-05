"""Predict nonnegative optimality gaps above certified lower bounds with min-plus experts."""
import json,time,math
import numpy as np
import torch
from torch import nn
from architecture import ROOT
from interval_architecture_data import load_interval
from experiment_v21_neural import graph_embedding,numerical
from experiment_v7_teacher import score

class IntervalMinPlus(nn.Module):
    def __init__(self,n,routes):
        super().__init__();self.routes=routes;self.s=nn.Embedding(496,routes);self.t=nn.Embedding(496,routes)
        self.register_buffer('graph',torch.tensor(graph_embedding()))
        self.geo=nn.Sequential(nn.Linear(n+64,256),nn.SiLU(),nn.Linear(256,256),nn.SiLU(),nn.Linear(256,routes))
        nn.init.normal_(self.s.weight,std=.01);nn.init.normal_(self.t.weight,std=.01)
        nn.init.zeros_(self.geo[-1].weight);nn.init.zeros_(self.geo[-1].bias)
    def forward(self,x,p,tau):
        geometry=torch.cat((x,self.graph[p[:,0]],self.graph[p[:,1]]),1)
        costs=self.s(p[:,0])+self.t(p[:,1])+self.geo(geometry)
        residual=-tau*torch.logsumexp(-costs/tau,1)+tau*math.log(self.routes)
        return torch.nn.functional.softplus(residual)

def main():
    start=time.monotonic();torch.set_num_threads(2);device=torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    folder=ROOT/'out/v26';folder.mkdir(exist_ok=True);x,y,b,u,lower=load_interval('development');xv,yv,bv,uv,lv=load_interval('validation')
    a,va=numerical(x),numerical(xv);mean=a.mean(0);std=np.maximum(a.std(0),1);a=np.clip((a-mean)/std,-10,10);va=np.clip((va-mean)/std,-10,10)
    m=y>0;xx=torch.tensor(a[m],device=device);pp=torch.tensor(x[m,10:12],dtype=torch.long,device=device)
    yy=torch.tensor((y[m]-lower[m])/100,dtype=torch.float32,device=device);w=1/y[m];w/=w.mean();ww=torch.tensor(w,dtype=torch.float32,device=device)
    vx=torch.tensor(va,device=device);vp=torch.tensor(xv[:,10:12],dtype=torch.long,device=device);prior=np.load(ROOT/'out/v19/validation-1536.npy')
    results=[];np.savez(folder/'normalization.npz',mean=mean,std=std)
    print(json.dumps({'lower_exact':int((lv==yv).sum()),'gap_median':float(np.median(yv-lv)),'lower_violations':0}),flush=True)
    for routes in (64,128):
        torch.manual_seed(20261005);model=IntervalMinPlus(xx.shape[1],routes).to(device);opt=torch.optim.AdamW(model.parameters(),lr=.0015,weight_decay=1e-5)
        for epoch in range(1,129):
            tau=.03+.47*(1+math.cos(np.pi*epoch/128))/2;model.train()
            for idx in torch.randperm(len(xx),device=device).split(4096):
                opt.zero_grad(set_to_none=True);loss=(torch.abs(model(xx[idx],pp[idx],tau)-yy[idx])*ww[idx]).mean();loss.backward();opt.step()
            for group in opt.param_groups:group['lr']=.0001+.0014*(1+math.cos(np.pi*epoch/128))/2
            if epoch%8==0 or epoch==1:
                model.eval()
                with torch.no_grad():gap=torch.cat([model(vx[i:i+8192],vp[i:i+8192],tau).cpu() for i in range(0,len(vx),8192)]).numpy()
                pred=np.clip(np.rint(lv+100*gap),lv,uv);path=folder/f'interval-{routes}-{epoch}.pt'
                torch.save({'state':{k:v.detach().cpu() for k,v in model.state_dict().items()},'tau':tau,'routes':routes},path)
                for weight in (0.,.25,.5,.75):
                    final=np.clip(np.rint((1-weight)*pred+weight*prior),lv,uv)
                    item={'routes':routes,'epoch':epoch,'tau':tau,'v19_weight':weight,'validation_score':score(yv,final),'model':str(path.relative_to(ROOT)),'model_bytes':path.stat().st_size};results.append(item)
                    np.save(folder/f'validation-{routes}-{epoch}-{weight}.npy',final)
                print(json.dumps({'routes':routes,'epoch':epoch,'standalone_score':score(yv,pred),'best_so_far':max(r['validation_score'] for r in results),'elapsed':time.monotonic()-start}),flush=True)
                (ROOT/'reports/V26-interval-minplus.json').write_text(json.dumps({'fit_split':'development','holdout_used':False,'device':str(device),
                    'architecture':'Certified folded-port/line-gap lower bound + learned nonnegative min-plus optimality gap, clipped to witnessed upper bound.',
                    'lower_bound_violations':0,'baseline':score(yv,prior),'candidates':results,'best':max(results,key=lambda r:r['validation_score']),'elapsed_seconds':time.monotonic()-start},indent=2)+'\n')

if __name__=='__main__':main()
