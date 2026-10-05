"""Audit finite-window nominal recurrence and current anchor extrapolation."""
import json,struct
import numpy as np
from architecture import ROOT
path=ROOT/'out/architecture-benchmark/v76-periodic-transients.csv'
z=np.loadtxt(path,delimiter=',',skiprows=1,dtype=np.int32)
with (ROOT/'out/architecture-benchmark/periodic-dense.raw.bin').open('rb') as f:
    header=f.read(392)
ports=np.frombuffer(header[72:392],dtype='<u2')
a=np.memmap(ROOT/'out/architecture-benchmark/periodic-dense.raw.bin',mode='r',dtype='<u2',offset=392,shape=(160,496,59,71))
lookup={(int(s),int(t),int(x),int(y)):int(v) for s,t,x,y,v in z}
rows=[]
for lo,hi in ((24,35),(36,47),(48,59),(60,71),(72,83)):
    for sign in (-1,1):
        chosen=z[(np.abs(z[:,3])>=lo)&(np.abs(z[:,3])<=hi)&(np.sign(z[:,3])==sign)]
        delta=[];err=[]
        for si,ti,x,y,value in chosen:
            previous=lookup.get((int(si),int(ti),int(x),int(y-sign*12)))
            if previous is not None and value<65535 and previous<65535:delta.append(int(value)-previous-(127 if sign>0 else 125))
            ay=abs(int(y));q=(ay-24)//12 if ay>35 else 0;anchor=sign*(ay-q*12)
            estimate=int(a[si,ports[ti],x+29,anchor+35])+q*(127 if sign>0 else 125)
            if value<65535 and estimate<65535:err.append(estimate-int(value))
        delta=np.array(delta);err=np.array(err)
        rows.append({'distance_band':[lo,hi],'vertical_sign':sign,'recurrence_pairs':len(delta),
                     'exact_periodic_fraction':float(np.mean(delta==0)),'recurrence_max_abs_error_ps':int(np.max(np.abs(delta))),
                     'anchor_exact_fraction':float(np.mean(err==0)),'anchor_mean_abs_error_ps':float(np.mean(np.abs(err))),
                     'anchor_underestimate_fraction':float(np.mean(err<0)),'anchor_max_abs_error_ps':int(np.max(np.abs(err)))})
report={'architecture_only':True,'golden_labels_used':False,'source_port_indices':[0,80,159],'targets':160,'horizontal_offsets':[-29,-20,-10,0,10,20,29],
        'finite_window_radius':112,'rows':len(z),'bands':rows,
        'scope':'Finite nominal graph recurrence evidence, not infinite-graph proof or physical-boundary/obstacle accuracy. Current anchors from radius48 graph; extended values from radius112.'}
(ROOT/'reports/V76-periodic-transients.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
