"""Finite ideal landmark-conditioned physical boundary penalties."""
import struct
import numpy as np
from boundary_potential_features import grid,arch
from architecture import ROOT
path=ROOT/'out/v196/field.raw'
with path.open('rb') as f:
    h=f.read(96)
    assert h[:8]==b'PHIPH001'
    assert struct.unpack('<6I',h[72:96])==(4,2,2,len(arch.instances),160,4)
field=np.memmap(path,dtype='<i2',mode='r',offset=96,shape=(4,2,2,len(arch.instances),160,4))

def phase_potentials(a):
    out=[]
    for x,y,port in [(109,110,99),(2,3,100)]:
        sx,sy,p=a[:,x].astype(int),a[:,y].astype(int),a[:,port].astype(int)
        mask=(p>=0)&(p<160)&(sx>=0)&(sx<120)&(sy>=0)&(sy<550)
        ids=np.full(len(a),-1,np.int32);ids[mask]=grid[sx[mask],sy[mask]];mask&=ids>=0
        values=np.zeros((len(a),64),np.float32)
        values[mask]=field[:,:,:,ids[mask],p[mask],:].transpose(3,0,1,2,4).reshape(-1,64)/12
        out.append(values)
    return np.column_stack(out)
