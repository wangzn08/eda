"""Certified lower bounds from folded port graphs and compressed x potentials."""
import csv,json
import numpy as np
from architecture import Architecture,ROOT
from evaluate import metrics

def main():
    arch=Architecture();n=len(arch.ports);matrices=[];slopes=[]
    if any(b['vertical crossable'] or (b['horizontal crossable'] and (b['left'],b['right'])!=(76,89)) for b in arch.blocks):
        raise ValueError('Potential proof requires the official horizontal crossing strip')
    for ax,ay in ((150,125),(150,-125),(-150,125),(-150,-125)):
        d=np.full((n,n),10**12,dtype=np.int64);np.fill_diagonal(d,0)
        for arc in arch.arcs:
            s,t=arch.port_ids[arc['from']],arch.port_ids[arc['to']];d[s,t]=min(d[s,t],12*arc['delay'])
        for net in arch.nets:
            s,t=arch.port_ids[net['from']],arch.port_ids[net['to']]
            # Vertical displacement is exact. Horizontal potential can shrink
            # across the globally compressed strip, so use its maximum change.
            potential=max(0,ax*net['delta x']) if net['delta x'] else ay*net['delta y']
            d[s,t]=min(d[s,t],12*net.get('delay',0)-potential)
        for k in range(n):np.minimum(d,d[:,k,None]+d[None,k,:],out=d)
        if np.min(np.diag(d))<0:raise ValueError('Negative folded cycle: chosen slope not certified')
        if d.min()<-32768:raise ValueError('Lower bound needs wider encoding')
        matrices.append(np.minimum(d,32767).astype(np.int16));slopes.append((ax,ay))
    header=ROOT/'out/v15/potential_lower_model.hpp'
    header.parent.mkdir(parents=True,exist_ok=True)
    lines=['// Architecture-derived admissible scaled potentials; no labels used.','#pragma once','#include <array>','#include <cstdint>','namespace potential_lower_model {',
      'constexpr std::array<int,4> ax={150,150,-150,-150};','constexpr std::array<int,4> ay={125,-125,125,-125};',
      f'constexpr std::array<int16_t,{4*n*n}> distance={{']
    values=np.concatenate([m.ravel() for m in matrices])
    lines.extend('  '+','.join(map(str,values[i:i+48]))+',' for i in range(0,len(values),48));lines+=['};','}'];header.write_text('\n'.join(lines)+'\n')
    root=ROOT/'out/evaluation';data=np.load(root/'validation.v4-features.npz');x=data['x'];y=data['truth'];sx,sy,tx,ty=x[:,:4].astype(np.int64).T
    phis=sx-np.clip(sx-76,0,14);phit=tx-np.clip(tx-76,0,14);sp=x[:,10].astype(int);tp=x[:,11].astype(int)
    lower=np.zeros(len(y),dtype=np.int64)
    for (ax,ay),d in zip(slopes,matrices):lower=np.maximum(lower,(ax*(phit-phis)+ay*(ty-sy)+d[sp,tp].astype(np.int64)+11)//12)
    violations=np.flatnonzero(lower>y)
    if len(violations):raise ValueError(f'Invalid lower bound: {len(violations)} examples {violations[:10]}')
    truth=list(csv.DictReader((root/'validation.golden.csv').open()));prior=list(csv.DictReader((root/'validation.v14-cpp.csv').open()));out=[];changed=0
    for g,r,l in zip(truth,prior,lower):
        row=dict(r);row['delay']=str(max(int(r['delay']),int(l)));changed+=row['delay']!=r['delay'];out.append(row)
    with (root/'validation.v15-interval.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=('From','To','delay'));w.writeheader();w.writerows(out)
    report={'before':metrics(truth,prior),'after':metrics(truth,out),'lower_bound_violations':0,'changed_rows':changed,
       'lower_exact_matches':int((lower==y).sum()),'source_bytes':header.stat().st_size,'parameter_bytes':int(values.nbytes),
       'fit_used_golden':False,'holdout_used':False,'slopes_scaled_by_12':slopes,'integrated_into_cpp_candidate':False,
       'proof':'Folded edge cost subtracts a maximum possible potential increase; shortest folded costs lower-bound every actual reweighted route.'}
    (ROOT/'reports/V15-potential-bounds.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
