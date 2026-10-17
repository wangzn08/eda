"""Route-factor median backfitting; labels used only from development."""
import json,time
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v120';out.mkdir(exist_ok=True);z=np.load(ROOT/'out/v117/route-data.npz');x,y,_,_=load('development');v,yv,_,_=load('validation');b,bv=z['development_base'],z['validation_base'];r,rv=z['development'].astype(np.int64),z['validation'].astype(np.int64)
def keys(x,r):
 sf=r[:,0]//8;tf=r[:,1]//8;pair=sf*20+tf;lane=(r[:,0]-r[:,1])%8;phase=(r[:,6]%10)*12+r[:,7]%12;direction=(r[:,3]>0)*2+(r[:,2]>0);kind=np.minimum(r[:,8],2);yb=np.minimum(r[:,5],7);sx=x[:,0].astype(np.int64);sy=x[:,1].astype(np.int64);tx=x[:,2].astype(np.int64);ty=x[:,3].astype(np.int64)
 return [(pair*8+lane)*120+phase,((pair*4+direction)*8+yb)*3+kind,((sf*120+phase)*8+yb)*3+kind,((tf*120+phase)*8+yb)*3+kind,((pair*100+sy%100)*3+kind),((tf*100+ty%100)*4+direction),((sf*120+np.minimum(sx,119-sx))*3+kind),((tf*120+np.minimum(tx,119-tx))*3+kind)]
a,av=keys(x,r),keys(v,rv);w=1000/np.maximum(y,1);report={'state':'running','fit_split':'development','holdout_used':False,'prediction_cache':False,'architecture':'Additive weighted-median factors of selected route family, relative lanes, phase, distance bucket, and boundary context','candidates':[]};start=time.monotonic()
for mincount in (4,12,32):
 tables=[];train=np.zeros(len(y));valid=np.zeros(len(yv))
 for i,k in enumerate(a):
  unique,inv=np.unique(k,return_inverse=True);tables.append({'unique':unique,'inv':inv,'value':np.zeros(len(unique)),'count':np.bincount(inv)})
 for epoch in range(3):
  for i,(k,kv,t) in enumerate(zip(a,av,tables)):
   previous=t['value'][t['inv']];train-=previous;res=y-b-train;order=np.lexsort((res,t['inv']));ids=t['inv'][order];starts=np.r_[0,np.flatnonzero(ids[1:]!=ids[:-1])+1];ends=np.r_[starts[1:],len(ids)];cum=np.cumsum(w[order]);offset=np.r_[0,cum[ends[:-1]-1]];threshold=offset+(cum[ends-1]-offset)*.5;pos=np.searchsorted(cum,threshold);values=res[order[pos]];values[t['count']<mincount]=0;t['value']=.7*values+.3*t['value'];train+=t['value'][t['inv']]
  valid[:]=0
  for kv,t in zip(av,tables):
   pos=np.searchsorted(t['unique'],kv);ok=pos<len(t['unique']);ok &= t['unique'][np.minimum(pos,len(t['unique'])-1)]==kv;valid[ok]+=t['value'][pos[ok]]
  p=np.rint(np.maximum(0,bv+valid));item={'mincount':mincount,'epoch':epoch+1,'validation_score':score(yv,p),'development_score':score(y,np.rint(np.maximum(0,b+train))),'elapsed':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True)
 np.save(out/f'm{mincount}.npy',p);np.savez(out/f'm{mincount}.npz',**{f'keys{i}':t['unique'] for i,t in enumerate(tables)},**{f'values{i}':t['value'] for i,t in enumerate(tables)})
 (ROOT/'reports/V120-route-tables.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V120-route-tables.json').write_text(json.dumps(report,indent=2)+'\n')
