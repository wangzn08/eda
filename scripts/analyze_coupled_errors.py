"""Full validation diagnostic; no holdout and no model fitting."""
import csv,json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
x,y,_,_=load('validation')
with (ROOT/'out/evaluation/validation.v82-128.csv').open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
m=y>0;e=np.abs(p-y)/np.maximum(y,1);loss=np.tanh(4*e);items=[]
for axis,col,bins in [('x',6,[0,10,30,60,120]),('y',7,[0,12,36,72,144,550])]:
 for lo,hi in zip(bins,bins[1:]):
  z=m&(x[:,col]>=lo)&(x[:,col]<hi)
  items.append({'axis':axis,'minimum':lo,'maximum_exclusive':hi,'rows':int(z.sum()),'score':float(100*(1-loss[z].mean())) if z.any() else None,'total_score_loss_contribution':float(100*loss[z].sum()/m.sum()),'relative_error_p95':float(np.quantile(e[z],.95)) if z.any() else None})
r={'split':'validation','holdout_used':False,'model':'V82 trees128','distance_bins':items,'scope':'Diagnostic only; repeated validation research selection, not independent hidden score.'}
(ROOT/'reports/V83-coupled-error-diagnosis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
