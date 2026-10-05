"""PDB anchored min-plus experts with small ReLU geometry and compiled phases.
Development labels only; wait for the current CPU benchmark before training.
"""
import argparse,json,math,time,os
import numpy as np
import torch
from torch import nn
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features,lower
from experiment_v7_teacher import score

class TinyRoutes(nn.Module):
    def __init__(self,n,hidden,routes):
        super().__init__();self.hidden=hidden;self.routes=routes
        self.s=nn.Embedding(496,routes);self.t=nn.Embedding(496,routes)
        self.ps=nn.Embedding(496,8);self.pt=nn.Embedding(496,8)
        self.sx=nn.Parameter(torch.randn(10,8,routes)*.02);self.sy=nn.Parameter(torch.randn(12,8,routes)*.02)
        self.tx=nn.Parameter(torch.randn(10,8,routes)*.02);self.ty=nn.Parameter(torch.randn(12,8,routes)*.02)
        self.geo=nn.Sequential(nn.Linear(n,hidden),nn.ReLU(),nn.Linear(hidden,hidden),nn.ReLU(),nn.Linear(hidden,routes))
        nn.init.normal_(self.s.weight,std=.03);nn.init.normal_(self.t.weight,std=.03)
        nn.init.zeros_(self.geo[-1].weight);nn.init.constant_(self.geo[-1].bias,.5)
    def costs(self,x,p):
        a,b=self.ps(p[:,0]),self.pt(p[:,1]);phase=(a[:,:,None]*self.sx[p[:,2]]).sum(1)+(a[:,:,None]*self.sy[p[:,3]]).sum(1)
        phase+=(b[:,:,None]*self.tx[p[:,2]]).sum(1)+(b[:,:,None]*self.ty[p[:,3]]).sum(1)
        return self.geo(x)+self.s(p[:,0])+self.t(p[:,1])+phase
    def forward(self,x,p,tau=0):
        c=self.costs(x,p)
        return -tau*torch.logsumexp(-c/tau,1)+tau*math.log(self.routes) if tau else c.amin(1)


def wait_benchmark():
    path=ROOT/'reports/V50-billion-no-cache.json'
    while True:
        report=json.loads(path.read_text())
        if report['state']=='complete':return
        if report['state'] in ('failed','timeout'):raise RuntimeError('Prior CPU benchmark failed; inspect before proceeding')
        print(json.dumps({'phase':'waiting_for_cpu_benchmark','state':report['state']}),flush=True)
        time.sleep(30)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wait-benchmark',action='store_true');parser.add_argument('--epochs',type=int,default=128);args=parser.parse_args()
    if args.wait_benchmark:wait_benchmark()
    begin=time.monotonic();torch.set_num_threads(1)
    device=torch.device('mps' if torch.backends.mps.is_available() else 'cpu');folder=ROOT/'out/v51';folder.mkdir(exist_ok=True)
    x,y,_,_=load('development');xv,yv,_,_=load('validation');lo=lower('development');lv=lower('validation');a,av=features(x,lo),features(xv,lv)
    mean=a.mean(0);std=np.maximum(a.std(0),1);a=np.clip((a-mean)/std,-10,10);av=np.clip((av-mean)/std,-10,10)
    np.savez(folder/'normalization.npz',mean=mean,std=std);m=y>0
    xx=torch.tensor(a[m],device=device);pp=torch.tensor(np.column_stack((x[m,10:12],x[m,35]%10,x[m,36]%12)),dtype=torch.long,device=device)
    yy=torch.tensor((y[m]-lo[m])/100,dtype=torch.float32,device=device);w=1/y[m];w/=w.mean();ww=torch.tensor(w,dtype=torch.float32,device=device)
    vx=torch.tensor(av,device=device);vp=torch.tensor(np.column_stack((xv[:,10:12],xv[:,35]%10,xv[:,36]%12)),dtype=torch.long,device=device)
    report={'fit_split':'development','selection_split':'validation','holdout_used':False,'device':str(device),'architecture':'PDB anchored hard-min latent route experts; small ReLU geometry; endpoint-phase factors compiled to int16 lookup tables for CPU inference; latent routes are not path witnesses','candidates':[]}
    for hidden,routes in [(64,128),(128,128),(64,64)]:
        torch.manual_seed(20261006+hidden+routes);model=TinyRoutes(xx.shape[1],hidden,routes).to(device);opt=torch.optim.AdamW(model.parameters(),lr=.002,weight_decay=1e-5)
        for epoch in range(1,args.epochs+1):
            tau=.20*(1+math.cos(math.pi*min(epoch,args.epochs*.75)/(args.epochs*.75)))/2 if epoch<=args.epochs*.75 else 0
            model.train()
            for idx in torch.randperm(len(xx),device=device).split(8192):
                opt.zero_grad(set_to_none=True);loss=(torch.abs(model(xx[idx],pp[idx],tau)-yy[idx])*ww[idx]).mean();loss.backward();opt.step()
            for group in opt.param_groups:group['lr']=.0001+.0019*(1+math.cos(math.pi*epoch/args.epochs))/2
            if epoch==1 or epoch%8==0:
                model.eval()
                with torch.no_grad():gap=torch.cat([model(vx[i:i+8192],vp[i:i+8192],0).cpu() for i in range(0,len(vx),8192)]).numpy()
                pred=np.rint(lv+np.maximum(0,100*gap));name=f'h{hidden}-r{routes}-e{epoch}';path=folder/f'{name}.pt'
                torch.save({'state':{k:v.detach().cpu() for k,v in model.state_dict().items()},'hidden':hidden,'routes':routes,'numeric':xx.shape[1],'mean':mean,'std':std,'epoch':epoch},path)
                np.save(folder/f'{name}.npy',pred);item={'hidden':hidden,'routes':routes,'epoch':epoch,'validation_score':score(yv,pred),'weights':str(path.relative_to(ROOT)),'unquantized_weights_bytes':path.stat().st_size,'estimated_int16_phase_table_bytes':2*496*120*routes*2,'elapsed_seconds':time.monotonic()-begin};report['candidates'].append(item);report['best']=max(report['candidates'],key=lambda r:r['validation_score']);(ROOT/'reports/V51-tiny-routes.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(item),flush=True)
    report['state']='complete';report['elapsed_seconds']=time.monotonic()-begin;(ROOT/'reports/V51-tiny-routes.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
