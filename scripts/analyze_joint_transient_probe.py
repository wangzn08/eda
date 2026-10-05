"""Analyze independent three-source directional/joint architecture probe."""
import json
import numpy as np
from architecture import ROOT
p=ROOT/'out/architecture-benchmark/joint-transient-probe.csv';a=np.genfromtxt(p,delimiter=',',names=True,dtype=np.int32)
items=[]
for group,name in enumerate(('vertical_long','horizontal_long','both_long')):
 for sx in (-1,1):
  for sy in (-1,1):
   m=(a['group']==group)&(np.sign(a['dx'])==sx)&(np.sign(a['dy'])==sy);e=a['prediction'][m].astype(np.int64)-a['nominal_truth'][m]
   items.append({'group':name,'x_direction':sx,'y_direction':sy,'rows':int(m.sum()),'mean_absolute_error_ps':float(np.abs(e).mean()),'mean_signed_error_ps':float(e.mean()),'p95_absolute_error_ps':float(np.quantile(np.abs(e),.95)),'exact_fraction':float((e==0).mean())})
e=(a['prediction'].astype(np.int64)-a['nominal_truth']).reshape(-1,3)
assert np.array_equal(a['group'].reshape(-1,3),np.tile(np.arange(3),(len(e),1)))
extra=e[:,2]-e[:,0]-e[:,1]
r={'architecture_only':True,'golden_labels_used':False,'source_indices':[0,80,159],'target_ports':160,'domain_radius':144,'cost_limit':5000,'comparisons':items,'joint_error_beyond_controls':{'mean_absolute_ps':float(np.abs(extra).mean()),'mean_signed_ps':float(extra.mean()),'p95_absolute_ps':float(np.quantile(np.abs(extra),.95))},'scope':'691200 independent nominal finite-graph cases atx70..79/y96..107 and directional controls. Three source ports only, no physical route or full-validation accuracy claim; extra error is diagnostic, not proof of unique causal decomposition.'}
(ROOT/'reports/V91-joint-transient-diagnosis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
