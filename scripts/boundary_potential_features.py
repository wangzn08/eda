"""Geometry-derived min-plus mobility penalties, without golden labels."""
import struct
import numpy as np
from architecture import ROOT,Architecture

arch=Architecture()
grid=np.full((120,550),-1,np.int32)
for i,site in enumerate(arch.instances):grid[site['x'],site['y']]=i
with (ROOT/'out/v193/field.raw').open('rb') as f:
    h=f.read(92);assert h[:8]==b'PHIPEN01'
    assert struct.unpack('<5I',h[72:92])==(2,3,len(arch.instances),160,4)
field=np.memmap(ROOT/'out/v193/field.raw',dtype='<i2',mode='r',offset=92,shape=(2,3,len(arch.instances),160,4))

def node_potentials(sx,sy,p):
    sx,sy,p=[np.asarray(v,dtype=np.int32) for v in (sx,sy,p)]
    mask=(p>=0)&(p<160)&(sx>=0)&(sx<120)&(sy>=0)&(sy<550)
    ids=np.full(len(p),-1,np.int32);ids[mask]=grid[sx[mask],sy[mask]];mask&=ids>=0
    values=np.zeros((len(p),24),np.float32)
    values[mask]=field[:,:,ids[mask],p[mask],:].transpose(2,0,1,3).reshape(-1,24)/12
    return values

def potentials(a):
    out=[]
    for x,y,port in [(109,110,99),(2,3,100)]:
        out.append(node_potentials(a[:,x],a[:,y],a[:,port]))
    return np.column_stack(out)
