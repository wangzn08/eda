"""Architecture-only endpoint connectivity and wire-lattice features."""
import numpy as np
from architecture import Architecture
from v4_features import NAMES

EXTRA_NAMES=('first_dx','first_dy','last_dx','last_dy','remaining_dx','remaining_dy',
 'remaining_abs_dx','remaining_abs_dy','remaining_dx_mod12','remaining_dy_mod12',
 'remaining_dx_mod4','remaining_dy_mod4','source_lane','target_lane','relaxed_port_distance',
 'source_access_e','source_access_w','source_access_n','source_access_s',
 'target_access_e','target_access_w','target_access_n','target_access_s',
 'source_boundary_x','source_boundary_y','target_boundary_x','target_boundary_y',
 'source_adjusted_x_mod10','target_adjusted_x_mod10',
 'source_adjusted_y_mod12','target_adjusted_y_mod12')

def augment(x):
    arch=Architecture();n=len(arch.ports)
    first=np.zeros((n,2));last=np.zeros((n,2))
    d=np.full((n,n),1e7);np.fill_diagonal(d,0)
    for a in arch.arcs:
        s,t=arch.port_ids[a['from']],arch.port_ids[a['to']]
        d[s,t]=min(d[s,t],a['delay'])
    nets=[]
    for net in arch.nets:
        s,t=arch.port_ids[net['from']],arch.port_ids[net['to']]
        v=(net['delta x'],net['delta y']);first[s]=v;last[t]=v
        d[s,t]=min(d[s,t],net.get('delay',0));nets.append((s,t,v))
    for k in range(n):np.minimum(d,d[:,k,None]+d[None,k,:],out=d)
    access=np.full((n,4),1e7);terminal=np.full((n,4),1e7)
    for s,t,(dx,dy) in nets:
        direction=0 if dx>0 else 1 if dx<0 else 2 if dy>0 else 3
        access[:,direction]=np.minimum(access[:,direction],d[:,s])
        terminal[:,direction]=np.minimum(terminal[:,direction],d[t,:])
    sp=x[:,NAMES.index('source_port')].astype(int);tp=x[:,NAMES.index('target_port')].astype(int)
    f=first[sp];l=last[tp];rx=x[:,4]-f[:,0]-l[:,0];ry=x[:,5]-f[:,1]-l[:,1]
    sx,sy,tx,ty=x[:,:4].T
    cols=[f[:,0],f[:,1],l[:,0],l[:,1],rx,ry,abs(rx),abs(ry),rx%12,ry%12,rx%4,ry%4,
          sp%8,tp%8,d[sp,tp],*[access[sp,i] for i in range(4)],*[terminal[tp,i] for i in range(4)],
          np.minimum(sx,arch.width-1-sx),np.minimum(sy,arch.height-1-sy),
          np.minimum(tx,arch.width-1-tx),np.minimum(ty,arch.height-1-ty),
          (sx+f[:,0])%10,(tx-l[:,0])%10,(sy+f[:,1])%12,(ty-l[:,1])%12]
    assert len(cols)==len(EXTRA_NAMES)
    return np.column_stack((x,*cols)).astype(np.float32)
