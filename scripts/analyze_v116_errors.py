import csv,json
import numpy as np
from architecture import ROOT,Architecture
from architecture_benchmark_data import load
x,y,_,_=load('validation')
with (ROOT/'out/v116/profile/validation.csv').open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
loss=np.tanh(4*np.abs(p-y)/np.maximum(y,1));cross=(np.minimum(x[:,0],x[:,2])<76)&(np.maximum(x[:,0],x[:,2])>89)
items=[]
def row(name,z):
 z=z&(y>0)
 if not z.any():return
 items.append({'group':name,'rows':int(z.sum()),'score':float(100*(1-loss[z].mean())),'score_loss':float(100*loss[z].sum()/len(y)),'mean_signed_error':float((p[z]-y[z]).mean()),'exact_fraction':float((p[z]==y[z]).mean()),'abs_error_p99':float(np.quantile(abs(p[z]-y[z]),.99))})
for name,z in [('cross',cross),('normal',~cross),('long_xy',(x[:,6]>=30)&(x[:,7]>=36)&~cross),('long_y',(x[:,6]<30)&(x[:,7]>=36)&~cross),('long_x',(x[:,6]>=30)&(x[:,7]<36)&~cross),('near',(x[:,6]<30)&(x[:,7]<36)&~cross),('edge_x',(np.minimum(x[:,0],x[:,2])<10)|(np.maximum(x[:,0],x[:,2])>109)),('edge_y',(np.minimum(x[:,1],x[:,3])<12)|(np.maximum(x[:,1],x[:,3])>537)),('over',p>y),('under',p<y)]:row(name,z)
arch=Architecture()
for key,col in [('source',10),('target',11)]:
 for n,port in enumerate(arch.ports):row(key+':'+port['Name'],x[:,col]==n)
items.sort(key=lambda r:-r['score_loss']);report={'validation_score':100*(1-loss.mean()),'exact_fraction':float((p==y).mean()),'groups':items,'holdout_used':False,'purpose':'diagnosis, not validation-label fitting'}
(ROOT/'reports/V117-error-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'summary':report['validation_score'],'groups':items[:25]},indent=2))
