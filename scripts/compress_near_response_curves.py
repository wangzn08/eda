"""Streaming global dictionary of exact late curves; bounded research working set."""
import json,lzma,struct,time,hashlib
import numpy as np
from architecture import ROOT
folder=ROOT/'out/v168';path=folder/'near.raw.bin'
with path.open('rb') as f:header=f.read(1056)
assert header[:8]==b'CURVRAW2';assert np.frombuffer(header,dtype='<u4',offset=392,count=6).tolist()==[160,160,59,24,40,2];assert np.array_equal(np.frombuffer(header,dtype='<u4',offset=416,count=160),np.arange(160))
assert path.stat().st_size==1056+160*160*59*24*40*2
source_curves=160*59*24;count=160*source_curves
def source_values(source):return np.memmap(path,dtype='<i2',mode='r',offset=1056+source*source_curves*40*2,shape=(source_curves,40))
offsets=np.empty(count,dtype='<i2');codes=np.empty(count,dtype='<u4');catalog={};patterns=[];start=time.monotonic()
for source in range(160):
 source_map=source_values(source);part=np.array(source_map,copy=True);del source_map
 base=part[:,0].copy();wide=part.astype(np.int32)-base[:,None];assert wide.min()>=-32768 and wide.max()<=32767;normalized=wide.astype('<i2');del wide
 unique,local=np.unique(normalized,axis=0,return_inverse=True);mapping=np.empty(len(unique),dtype='<u4')
 for k,row in enumerate(unique):
  key=row.tobytes();index=catalog.get(key)
  if index is None:index=len(patterns);catalog[key]=index;patterns.append(key)
  mapping[k]=index
 lo=source*len(part);hi=lo+len(part);offsets[lo:hi]=base;codes[lo:hi]=mapping[local]
 assert np.array_equal(unique[local],normalized)
 print(json.dumps({'source':source,'global_patterns':len(patterns),'elapsed_seconds':time.monotonic()-start}),flush=True)
dtype='<u2' if len(patterns)<=65536 else '<u4';codes=codes.astype(dtype);table=np.frombuffer(b''.join(patterns),dtype='<i2').reshape(-1,40)
metadata=struct.pack('<6I',160,160,59,24,40,8)+struct.pack('<2I',len(patterns),codes.dtype.itemsize)
payload=offsets.tobytes()+table.astype('<i2').tobytes()+codes.tobytes();compressed=lzma.compress(payload,preset=3)
asset=b'CVNEAR01'+header[8:392]+metadata+compressed;(folder/'near-curves.bin').write_bytes(asset)
decoded=lzma.decompress(compressed);assert decoded==payload
for source in range(160):
 source_map=source_values(source);lo=source*source_curves
 for i in range(0,source_curves,65536):
  j=min(i+65536,source_curves);assert np.array_equal((table[codes[lo+i:lo+j]].astype(np.int32)+offsets[lo+i:lo+j,None]).astype('<i2'),source_map[i:j])
 del source_map
r={'state':'complete','scope':'Architecture-only finite ideal-graph near-x late curves; native accuracy and timing pending','curves':count,'unique_patterns':len(patterns),'index_bytes':codes.dtype.itemsize,'asset_bytes':len(asset),'decoded_bytes':len(payload),'roundtrip_exact':True,'asset_sha256':hashlib.sha256(asset).hexdigest(),'elapsed_seconds':time.monotonic()-start};(ROOT/'reports/V168-near-response-curves-storage.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
