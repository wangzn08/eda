"""Architecture curve and obstruction features, independent of fitting.
"""
import lzma,struct
import numpy as np
from architecture import ROOT
from physics_response_features import enrich
raw=(ROOT/'out/v168/near-curves.bin').read_bytes();assert raw[:8]==b'CVNEAR01';npatterns,width=struct.unpack('<2I',raw[416:424]);count=160*160*59*24;data=lzma.decompress(raw[424:]);offsets=np.frombuffer(data,dtype='<i2',count=count);patterns=np.frombuffer(data,dtype='<i2',count=npatterns*40,offset=count*2).reshape(-1,40);codes=np.frombuffer(data,dtype='<u4' if width==4 else '<u2',count=count,offset=count*2+npatterns*80)
def features(a):
 s=a[:,99].astype(int);t=a[:,100].astype(int);dx=a[:,101].astype(int);dy=a[:,102].astype(int);q=abs(dy)//12;r=abs(dy)%12
 mask=(s>=0)&(s<160)&(t>=0)&(t<160)&(abs(dx)<=29)&(q>=8)&(q<48)&(a[:,107]<=2);k=np.flatnonzero(mask);pos=(((s[k]*160+t[k])*59+dx[k]+29)*24+(dy[k]>0)*12+r[k]);p=patterns[codes[pos]];base=offsets[pos];slope=np.where(dy[k]>0,127,125)
 response=np.zeros((len(a),9),np.float32);current=base+p[np.arange(len(k)),q[k]-8]+q[k]*slope
 # Trace starts at column 99: nominal_delay=112, terminal_cost=113.
 # Compare the new complete terminal estimate with the previous estimate.
 response[k,0]=current;response[k,1]=current+a[k,113]-a[k,112]
 for j,period in enumerate((8,20,32,47),2):response[k,j]=base+p[:,period-8]+period*slope
 lo=(q[k]-1).clip(8,47);hi=(q[k]+1).clip(8,47);below=base+p[np.arange(len(k)),lo-8]+lo*slope;above=base+p[np.arange(len(k)),hi-8]+hi*slope
 response[k,6]=current-below;response[k,7]=above-current;response[k,8]=above+below-2*current
 sx,sy,tx,ty=a[:,109],a[:,110],a[:,2],a[:,3];inside_s=(sx>=76)&(sx<=89);inside_t=(tx>=76)&(tx<=89);low=np.minimum(sy,ty);high=np.maximum(sy,ty)
 bands=np.zeros(len(a),np.float32)
 for y in range(0,550,100):bands+=((low<y+49)&(high>y)).astype(np.float32)
 geometry=np.column_stack((inside_s,inside_t,inside_s&inside_t,bands,bands*(inside_s|inside_t),np.minimum(sx-75,90-sx),np.minimum(tx-75,90-tx),(np.minimum(sx,tx)<16)&(np.minimum(sy,ty)<100),np.maximum(0,100-np.minimum(sy,ty)),np.maximum(0,16-np.minimum(sx,tx))))
 return np.column_stack((enrich(a),mask,response,geometry)).astype(np.float32)
