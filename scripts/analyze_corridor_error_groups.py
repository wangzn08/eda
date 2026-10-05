"""Full validation error diagnosis to choose next architecture; no holdout."""
import csv,json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
x,y,_,_=load('validation')
with (ROOT/'out/evaluation/validation.v89-64.csv').open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
m=y>0;loss=np.tanh(4*np.abs(p-y)/np.maximum(y,1));cross=(np.minimum(x[:,0],x[:,2])<76)&(np.maximum(x[:,0],x[:,2])>89)
items=[]
for name,z in [('block_crossing',cross),('no_block_crossing',~cross),('both_long',(x[:,6]>=30)&(x[:,7]>=36)),('short_x_long_y',(x[:,6]<30)&(x[:,7]>=36)),('short_y',x[:,7]<36)]:
 z=z&m;items.append({'group':name,'rows':int(z.sum()),'score':float(100*(1-loss[z].mean())),'total_score_loss_contribution':float(100*loss[z].sum()/m.sum()),'mean_signed_error_ps':float((p[z]-y[z]).mean())})
r={'model':'V89trees64','split':'validation','holdout_used':False,'groups':items,'scope':'Overlapping diagnostic groups, not fitting or independent test evidence.'}
(ROOT/'reports/V89-error-groups.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
