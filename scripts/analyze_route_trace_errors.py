import json,numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
z=np.load(ROOT/'out/v117/route-data.npz');r=z['validation'];p=z['validation_base'];x,y,_,_=load('validation');loss=np.tanh(4*abs(p-y)/np.maximum(y,1));items=[]
def add(name,m):
 if not m.any():return
 items.append({'group':name,'rows':int(m.sum()),'loss':float(100*loss[m].sum()/len(y)),'score':float(100*(1-loss[m].mean())),'signed':float((p[m]-y[m]).mean()),'exact':float((p[m]==y[m]).mean())})
for col,name in [(4,'qx'),(5,'qy'),(8,'kind')]:
 for val in np.unique(r[:,col]):add(f'{name}={int(val)}',r[:,col]==val)
for col,name in [(6,'rx'),(7,'ry')]:
 for val in np.unique(r[:,col]):add(f'{name}={int(val)}',r[:,col]==val)
for mname,m in [('normal',r[:,8]==0),('cross',r[:,8]>0)]:
 for q in range(15):add(f'{mname}/qy={q}',m&(r[:,5]==q))
items.sort(key=lambda a:-a['loss']);(ROOT/'reports/V117-route-error-slices.json').write_text(json.dumps(items,indent=2)+'\n');print(json.dumps(items[:32],indent=2))
