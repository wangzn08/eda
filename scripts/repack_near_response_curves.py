"""Lossless source/phase and byte-plane layout comparisons for curve dictionary."""
import json,lzma,struct,time
import numpy as np
from architecture import ROOT
folder=ROOT/'out/v168';raw=(folder/'near-curves.bin').read_bytes();h=raw[:424];assert h[:8]==b'CVNEAR01';npatterns,width=struct.unpack('<2I',h[416:424]);count=160*160*59*24;data=lzma.decompress(raw[424:]);assert len(data)==count*2+npatterns*80+count*width
offsets=np.frombuffer(data,dtype='<i2',count=count);patterns=data[count*2:count*2+npatterns*80];codes=np.frombuffer(data,dtype='<u2' if width==2 else '<u4',count=count,offset=count*2+npatterns*80).astype('<u4');assert codes.max()<npatterns
out=ROOT/'out/v169';out.mkdir(exist_ok=True);report={'state':'running','scope':'Lossless storage layout only; native parity and submission profile pending','candidates':[]};start=time.monotonic()
for flags in (0,2,1,3,7):
 c=codes;o=offsets
 if flags&1:c=c.reshape(160,160,59,24).transpose(1,2,3,0).reshape(-1);o=o.reshape(160,160,59,24).transpose(1,2,3,0).reshape(-1)
 b=c.astype('<u4').view(np.uint8).reshape(-1,4)[:,:3].copy();codebytes=b.T.copy().tobytes() if flags&2 else b.tobytes()
 ob=o.astype('<i2').view(np.uint8).reshape(-1,2);offsetbytes=ob.T.copy().tobytes() if flags&4 else ob.tobytes()
 payload=offsetbytes+patterns+codebytes;compressed=lzma.compress(payload,preset=3);assert lzma.decompress(compressed)==payload
 header=b'CVNEAR02'+h[8:420]+struct.pack('<I',3)+struct.pack('<I',flags);asset=header+compressed;(out/f'curves-layout-{flags}.bin').write_bytes(asset)
 # Reconstruct source-major codes and offsets before accepting each candidate.
 back=np.frombuffer(codebytes,dtype=np.uint8).reshape(3,-1).T if flags&2 else np.frombuffer(codebytes,dtype=np.uint8).reshape(-1,3)
 reconstructed=(back[:,0].astype(np.uint32)|(back[:,1].astype(np.uint32)<<8)|(back[:,2].astype(np.uint32)<<16));assert np.array_equal(reconstructed,c)
 backo=np.frombuffer(offsetbytes,dtype=np.uint8).reshape(2,-1).T.copy() if flags&4 else np.frombuffer(offsetbytes,dtype=np.uint8).reshape(-1,2).copy();assert np.array_equal(backo.view('<i2').ravel(),o)
 item={'flags':flags,'asset_bytes':len(asset),'roundtrip_exact':True,'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V169-curve-layout-storage.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V169-curve-layout-storage.json').write_text(json.dumps(report,indent=2)+'\n')
