"""Lossless differences along source dimension; no query-time reconstruction."""
import json,lzma,struct,time
import numpy as np
from architecture import ROOT
folder=ROOT/'out/v168';raw=(folder/'near-curves.bin').read_bytes();h=raw[:424];assert h[:8]==b'CVNEAR01';npatterns,width=struct.unpack('<2I',h[416:424]);count=160*160*59*24;data=lzma.decompress(raw[424:])
original_o=np.frombuffer(data,dtype='<i2',count=count).reshape(160,160,59,24).transpose(1,2,3,0).reshape(-1,160)
patterns=data[count*2:count*2+npatterns*80];original_c=np.frombuffer(data,dtype='<u4',count=count,offset=count*2+npatterns*80).reshape(160,160,59,24).transpose(1,2,3,0).reshape(-1,160)
out=ROOT/'out/v172';out.mkdir(exist_ok=True);start=time.monotonic();r={'state':'running','scope':'Lossless storage transform only; native parity pending','candidates':[]}
for flags in (15,23,31):
 o=original_o.copy();c=original_c.copy()
 if flags&8:o[:,1:]=(original_o[:,1:].astype(np.int32)-original_o[:,:-1].astype(np.int32)).astype('<i2')
 if flags&16:c[:,1:]=(original_c[:,1:]-original_c[:,:-1])&0xffffff
 ob=o.view(np.uint8).reshape(-1,2).T.copy().tobytes();cb=c.astype('<u4').view(np.uint8).reshape(-1,4)[:,:3].T.copy().tobytes();payload=ob+patterns+cb;compressed=lzma.compress(payload,preset=3);assert lzma.decompress(compressed)==payload
 for i in range(0,len(o),4096):
  j=min(i+4096,len(o));backo=o[i:j].astype(np.int64);backc=c[i:j].astype(np.uint64)
  if flags&8:backo=backo.cumsum(axis=1)
  if flags&16:backc=backc.cumsum(axis=1)&0xffffff
  assert np.array_equal(backo.astype('<i2'),original_o[i:j]);assert np.array_equal(backc.astype('<u4'),original_c[i:j])
 asset=b'CVNEAR02'+h[8:420]+struct.pack('<I',3)+struct.pack('<I',flags)+compressed;(out/f'curves-layout-{flags}.bin').write_bytes(asset)
 item={'flags':flags,'asset_bytes':len(asset),'roundtrip_exact':True,'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V172-curve-source-deltas.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V172-curve-source-deltas.json').write_text(json.dumps(r,indent=2)+'\n')
