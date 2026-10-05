"""Geometry-only out-of-range audit of port-specific transient slopes."""
import json
import numpy as np
from architecture import ROOT
z=np.loadtxt(ROOT/'out/architecture-benchmark/v76-periodic-transients.csv',delimiter=',',skiprows=1,dtype=np.int32)
values={(int(s),int(t),int(x),int(y)):int(v) for s,t,x,y,v in z}
results=[]
for sign in (-1,1):
    errors={k:[] for k in ('anchor24_cheapest','anchor48_cheapest','anchor48_measured_slope')}
    for s,t,x,y,value in z:
        if not 72<=abs(y)<=83 or np.sign(y)!=sign or value>=65535:continue
        residue=(abs(int(y))-24)%12;q=(abs(int(y))-(24+residue))//12
        key=(int(s),int(t),int(x));d24=values[(*key,sign*(24+residue))];d36=values[(*key,sign*(36+residue))];d48=values[(*key,sign*(48+residue))]
        c=127 if sign>0 else 125;slope=max(c,d48-d36)
        for name,p in [('anchor24_cheapest',d24+q*c),('anchor48_cheapest',d48+(q-2)*c),('anchor48_measured_slope',d48+(q-2)*slope)]:errors[name].append(p-int(value))
    for name,e in errors.items():
        a=np.array(e);results.append({'sign':sign,'method':name,'rows':len(a),'exact_fraction':float(np.mean(a==0)),
                                    'mean_abs_error_ps':float(np.mean(np.abs(a))),'max_abs_error_ps':int(np.max(np.abs(a)))})
r={'architecture_only':True,'golden_labels_used':False,'fit_geometry_band':[24,59],'evaluation_geometry_band':[72,83],
   'results':results,'scope':'Distance-band extrapolation in finite nominal graph for3 source ports and7 horizontal offsets; not real validation accuracy or feasible path certificate.'}
(ROOT/'reports/V76-transient-slopes.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
