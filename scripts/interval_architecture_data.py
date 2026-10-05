"""Architecture-derived admissible port potentials plus unavoidable line crossings."""
import numpy as np
from architecture import Architecture,ROOT
from architecture_benchmark_data import load

def potentials():
    a=Architecture()
    if any(b['vertical crossable'] or (b['horizontal crossable'] and (b['left'],b['right'])!=(76,89)) for b in a.blocks):
        raise ValueError('Potential proof requires the official horizontal crossing strip')
    path=ROOT/'out/architecture-benchmark/lower-potentials.npy'
    if path.exists():return np.load(path)
    n=len(a.ports);matrices=[]
    for ax,ay in ((150,125),(150,-125),(-150,125),(-150,-125)):
        d=np.full((n,n),10**12,dtype=np.int64);np.fill_diagonal(d,0)
        for arc in a.arcs:
            s,t=a.port_ids[arc['from']],a.port_ids[arc['to']];d[s,t]=min(d[s,t],12*arc['delay'])
        for net in a.nets:
            s,t=a.port_ids[net['from']],a.port_ids[net['to']]
            delta=max(0,ax*net['delta x']) if net['delta x'] else ay*net['delta y']
            d[s,t]=min(d[s,t],12*net.get('delay',0)-delta)
        for k in range(n):np.minimum(d,d[:,k,None]+d[None,k,:],out=d)
        assert np.min(np.diag(d))>=0
        matrices.append(d)
    result=np.array(matrices);np.save(path,result);return result

def load_interval(split):
    x,y,b,u=load(split);d=potentials();sx,sy,tx,ty=x[:,:4].astype(np.int64).T
    phi=lambda a:a-np.clip(a-76,0,14);dx=phi(tx)-phi(sx);dy=ty-sy;sp=x[:,10].astype(int);tp=x[:,11].astype(int)
    lower=np.zeros(len(y),dtype=np.int64)
    for k,(ax,ay) in enumerate(((150,125),(150,-125),(-150,125),(-150,-125))):
        lower=np.maximum(lower,(ax*dx+ay*dy+d[k,sp,tp]+11)//12)
    lower=lower+x[:,20]+x[:,21];assert np.all(lower<=y),'Lower-bound violation'
    finite=np.isfinite(u);span=np.where(finite,np.where(finite,u,0)-lower,0)
    extra=np.column_stack((lower,lower/np.maximum(b,1),span,span/np.maximum(b,1)))
    return np.column_stack((x,extra)).astype(np.float32),y,b,u,lower
