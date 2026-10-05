"""Residual neural models with learned ports and architecture graph embeddings."""
import json,time,math
import numpy as np
import torch
from torch import nn
from architecture import Architecture,ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score

def graph_embedding():
    a=Architecture();mat=np.zeros((496,496),dtype=np.float64)
    for arc in a.arcs:mat[a.port_ids[arc['from']],a.port_ids[arc['to']]]=math.exp(-arc['delay']/150)
    for net in a.nets:mat[a.port_ids[net['from']],a.port_ids[net['to']]]+=1
    mat=(mat+mat.T)/2;degree=np.maximum(mat.sum(1),1e-9)
    mat=mat/np.sqrt(degree[:,None]*degree[None,:]);w,v=np.linalg.eigh(mat)
    z=v[:,-32:]*np.sqrt(np.maximum(w[-32:],0))[None,:];z/=np.maximum(z.std(0),1e-6)
    return z.astype(np.float32)

class Model(nn.Module):
    def __init__(self,numeric,graph=False):
        super().__init__();self.s=nn.Embedding(496,48);self.t=nn.Embedding(496,48)
        self.register_buffer('graph',torch.tensor(graph_embedding()) if graph else torch.zeros(496,0))
        self.first=nn.Linear(numeric+144+(64 if graph else 0),384)
        self.blocks=nn.ModuleList([nn.Sequential(nn.Linear(384,384),nn.SiLU(),nn.Linear(384,384)) for _ in range(3)])
        self.head=nn.Linear(384,1);nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)
    def forward(self,x,p):
        a,b=self.s(p[:,0]),self.t(p[:,1]);parts=[x,a,b,a*b]
        if self.graph.shape[1]:parts.extend([self.graph[p[:,0]],self.graph[p[:,1]]])
        z=torch.nn.functional.silu(self.first(torch.cat(parts,1)))
        for block in self.blocks:z=torch.nn.functional.silu(z+block(z))
        return self.head(z).squeeze(1)

def numerical(x):
    cols=[x]
    for i,period in ((35,10),(36,12),(0,10),(1,12),(2,10),(3,12)):
        a=x[:,i]*(2*np.pi/period);cols.extend([np.sin(a)[:,None],np.cos(a)[:,None]])
    return np.concatenate(cols,1)

def main():
    start=time.monotonic();torch.set_num_threads(2);torch.manual_seed(20261005);np.random.seed(20261005)
    device=torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    folder=ROOT/'out/v23';folder.mkdir(exist_ok=True);x,y,b,u=load('development');xv,yv,bv,uv=load('validation')
    a,va=numerical(x),numerical(xv);mean=a.mean(0);std=np.maximum(a.std(0),1)
    a=np.clip((a-mean)/std,-10,10);va=np.clip((va-mean)/std,-10,10);np.savez(folder/'normalization.npz',mean=mean,std=std)
    m=(y>0)&(b>0);xx=torch.tensor(a[m],device=device);pp=torch.tensor(x[m,10:12],dtype=torch.long,device=device)
    yy=torch.tensor(100*(y[m]-b[m])/b[m],dtype=torch.float32,device=device);ww=torch.tensor(b[m]/y[m],dtype=torch.float32,device=device)
    vx=torch.tensor(va,device=device);vp=torch.tensor(xv[:,10:12],dtype=torch.long,device=device)
    prior=np.load(ROOT/'out/v19/validation-1536.npy');results=[]
    for graph in (True,):
        torch.manual_seed(20261005);model=Model(xx.shape[1],graph).to(device);optimizer=torch.optim.AdamW(model.parameters(),lr=.0015,weight_decay=1e-4)
        for epoch in range(1,121):
            model.train();order=torch.randperm(len(xx),device=device);running=0.
            for chunk in order.split(4096):
                optimizer.zero_grad(set_to_none=True);pred=model(xx[chunk],pp[chunk]);loss=(torch.abs(pred-yy[chunk])*ww[chunk]).mean();loss.backward();optimizer.step();running+=float(loss.detach().cpu())
            for g in optimizer.param_groups:g['lr']=.00015+.00135*(1+math.cos(np.pi*epoch/120))/2
            if epoch%8==0 or epoch==1:
                model.eval()
                with torch.no_grad():correction=torch.cat([model(vx[i:i+8192],vp[i:i+8192]).cpu() for i in range(0,len(vx),8192)]).numpy()
                raw=np.maximum(0,bv*(1+correction/100));pred=np.minimum(np.rint(raw),uv)
                path=folder/f'neural-{int(graph)}-{epoch}.pt';torch.save({k:v.detach().cpu() for k,v in model.state_dict().items()},path)
                for w in (0.,.25,.5,.75):
                    final=np.minimum(np.rint((1-w)*pred+w*prior),uv)
                    item={'graph_embedding':graph,'epoch':epoch,'v19_weight':w,'validation_score':score(yv,final),
                      'model':str(path.relative_to(ROOT)),'model_bytes':path.stat().st_size};results.append(item)
                    np.save(folder/f'validation-{int(graph)}-{epoch}-{w}.npy',final)
                print(json.dumps({'graph':graph,'epoch':epoch,'standalone_score':score(yv,pred),'best_so_far':max(z['validation_score'] for z in results),'elapsed_seconds':time.monotonic()-start}),flush=True)
                report={'fit_split':'development','holdout_used':False,'device':str(device),'baseline':score(yv,prior),
                    'architecture':'Port embeddings with multiplicative endpoint interaction, optional graph spectral embeddings, Fourier numerical features and three residual MLP blocks, width384 and 48-dimensional learned ports.',
                    'candidates':results,'best':max(results,key=lambda z:z['validation_score']),'elapsed_seconds':time.monotonic()-start}
                (ROOT/'reports/V23-neural-architecture.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
