"""Lossless architecture transient residual export; no request labels."""
import hashlib,json,struct,zlib
import numpy as np
from architecture import ROOT
raw=ROOT/'out/architecture-benchmark/vertical-transients.raw.bin'
header=raw.read_bytes()[:392];assert header[:8]==b'TRANSV01'
a=np.memmap(raw,mode='r',dtype='<i2',offset=392,shape=(160*160,59,48))
choices=[];best=None
for transform in (0,1,2):
    v=a.astype(np.int32)
    if transform>=1:v[:,1:,:]-=v[:,:-1,:].copy()
    if transform==2:v[:,:,1:]-=v[:,:,:-1].copy()
    assert v.min()>=-32768 and v.max()<=32767
    compressed=zlib.compress(v.astype('<i2').tobytes(),6)
    item={'transform':transform,'compressed_bytes':len(compressed)};choices.append(item);print(item,flush=True)
    if best is None or len(compressed)<len(best[1]):best=(transform,compressed)
transform,compressed=best
restored=np.frombuffer(zlib.decompress(compressed),dtype='<i2').reshape(a.shape).astype(np.int32)
if transform==2:restored=np.cumsum(restored,axis=2,dtype=np.int32)
if transform>=1:restored=np.cumsum(restored,axis=1,dtype=np.int32)
assert np.array_equal(restored,a)
asset=ROOT/'out/architecture-benchmark/vertical-transients.bin'
asset.write_bytes(b'TRVZL001'+header[8:]+struct.pack('<IQ',transform,a.nbytes)+compressed)
r={'architecture_only':True,'golden_labels_used':False,'decoded_values':a.size,'decoded_bytes':a.nbytes,
   'choices':choices,'selected_transform':transform,'exact_roundtrip':True,'asset_bytes':asset.stat().st_size,
   'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'combined_with_v59_runtime_bytes':asset.stat().st_size+93278137,
   'scope':'Adds36..59 vertical residuals to existing template; finite nominal graph, not a certified physical path.'}
(ROOT/'reports/V77-vertical-transient-export.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
