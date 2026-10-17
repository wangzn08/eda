"""Architecture-only transient response descriptors shared by student experiments."""
import numpy as np
from architecture import ROOT
tail=np.memmap(ROOT/'out/v147/tail.raw.bin',dtype='<i2',mode='r',offset=428,shape=(160,160,59,24,4))
joint=np.memmap(ROOT/'out/v137/multianchor.raw.bin',dtype='<i2',mode='r',offset=432,shape=(160,160,2,2,10,12,3,3))
def enrich(a):
 s=a[:,99].astype(int);t=a[:,100].astype(int);rx=a[:,105].astype(int);ry=a[:,106].astype(int);qy=a[:,104].astype(int)
 valid=(s>=0)&(s<160)&(t>=0)&(t<160)&(abs(rx)<=29)&(abs(ry)>=24)&(abs(ry)<=35)&(qy>6)
 knots=np.zeros((len(a),4),np.float32);k=np.flatnonzero(valid);knots[k]=tail[s[k],t[k],rx[k]+29,(ry[k]>0)*12+abs(ry[k])-24]
 endpoints=np.array([6,12,20,32,42]);hi=np.searchsorted(endpoints,qy,side='left').clip(1,4);lo=np.column_stack((np.zeros(len(a)),knots))
 d=lo[np.arange(len(a)),hi-1]+(lo[np.arange(len(a)),hi]-lo[np.arange(len(a)),hi-1])*(qy-endpoints[hi-1])/(endpoints[hi]-endpoints[hi-1]);d=np.where(valid,np.rint(d),0)
 validj=(s>=0)&(s<160)&(t>=0)&(t<160)&(abs(rx)>=20)&(abs(rx)<=29)&(abs(ry)>=24)&(abs(ry)<=35)&(a[:,103]>0)&(qy>0)
 j=np.zeros((len(a),9),np.float32);k=np.flatnonzero(validj);j[k]=joint[s[k],t[k],(rx[k]>0).astype(int),(ry[k]>0).astype(int),abs(rx[k])-20,abs(ry[k])-24].reshape(-1,9)
 return np.column_stack((a,valid,knots,d,knots[:,3]-knots[:,2],validj,j)).astype(np.float32)

