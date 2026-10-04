"""Long-wire access and direction-specific displacement residues."""
import numpy as np
from architecture import Architecture
from v9_topology_features import augment,EXTRA_NAMES
WIRE_NAMES=('remaining_dx_mod10','remaining_abs_dx_mod10','remaining_abs_dy_mod12',
 'long_source_access_e','long_source_access_w','long_source_access_n','long_source_access_s',
 'long_target_access_e','long_target_access_w','long_target_access_n','long_target_access_s')

def augment_wire(x):
    z=augment(x);arch=Architecture();n=len(arch.ports)
    d=np.full((n,n),1e7);np.fill_diagonal(d,0)
    for arc in arch.arcs:
        s,t=arch.port_ids[arc['from']],arch.port_ids[arc['to']];d[s,t]=min(d[s,t],arc['delay'])
    for net in arch.nets:
        s,t=arch.port_ids[net['from']],arch.port_ids[net['to']];d[s,t]=min(d[s,t],net.get('delay',0))
    for k in range(n):np.minimum(d,d[:,k,None]+d[None,k,:],out=d)
    access=np.full((n,4),1e7);terminal=np.full((n,4),1e7)
    for net in arch.nets:
        dx,dy=net['delta x'],net['delta y']
        if abs(dx)+abs(dy)<10:continue
        s,t=arch.port_ids[net['from']],arch.port_ids[net['to']]
        direction=0 if dx>0 else 1 if dx<0 else 2 if dy>0 else 3
        access[:,direction]=np.minimum(access[:,direction],d[:,s]);terminal[:,direction]=np.minimum(terminal[:,direction],d[t,:])
    sp=x[:,10].astype(int);tp=x[:,11].astype(int);rx=z[:,35];ry=z[:,36]
    return np.column_stack((z,rx%10,abs(rx)%10,abs(ry)%12,*[access[sp,i] for i in range(4)],*[terminal[tp,i] for i in range(4)])).astype(np.float32)
