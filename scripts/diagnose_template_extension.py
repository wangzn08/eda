"""Diagnose periodic-extension errors and candidate diversity, validation only."""
import csv
import json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
x,y,_,_=load('validation')
def read(name):
    with (ROOT/'out/evaluation'/name).open() as f:
        return np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
b=read('validation.v55-core.csv');p=read('validation.v59-profile.csv')
assert len(b)==len(p)==len(y)
dx=x[:,2]-x[:,0];dy=x[:,3]-x[:,1];dist=np.abs(dx)+np.abs(dy)
loss=np.tanh(4*np.abs(p-y)/np.maximum(y,1));bloss=np.tanh(4*np.abs(b-y)/np.maximum(y,1))
def summary(mask):
    return {'rows':int(mask.sum()),'score':float(100*(1-loss[mask].mean())),
            'mean_signed_error_ps':float((p-y)[mask].mean()),
            'mean_absolute_error_ps':float(np.abs(p-y)[mask].mean()),
            'remaining_loss_fraction':float(loss[mask].sum()/loss.sum()),
            'template_score':float(100*(1-bloss[mask].mean())),
            'template_better_fraction':float((bloss[mask]<loss[mask]).mean())}
groups={}
for lo,hi in ((0,30),(30,100),(100,200),(200,350),(350,10000)):
    for sign,name in ((dy>=0,'north'),(dy<0,'south')):
        mask=(dist>=lo)&(dist<hi)&sign
        if mask.any():groups[f'{lo}_{hi}_{name}']=summary(mask)
residues={str(i):summary((np.abs(dy).astype(int)%12)==i) for i in range(12)}
report={'split':'validation','holdout_used':False,'distance_direction':groups,'vertical_residues':residues,
        'baseline_score':float(100*(1-loss.mean())),
        'oracle_best_of_template_and_corrected_score':float(100*(1-np.minimum(loss,bloss).mean())),
        'oracle_scope':'Uses golden to choose; unattainable evaluation ceiling, not deployable model.',
        'candidate_disagreement_mean_ps':float(np.abs(p-b).mean())}
(ROOT/'reports/V61-template-extension-diagnostics.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
