"""Lossless architecture-only interaction patch with explicit baseline provenance."""
import hashlib,json,lzma,struct,time
import numpy as np
from architecture import ROOT
folder=ROOT/'out/architecture-benchmark';raw=folder/'joint-transient.raw.bin'
with raw.open('rb') as f:header=f.read(392)
assert header[:8]==b'TRJRAW01'
a=np.memmap(raw,mode='r',dtype='<i2',offset=392,shape=(160,160,2,2,10,12));decoded=a.tobytes()
files=['core-template-xz6.bin','vertical-transients-xz.bin','horizontal-transients.bin','vertical-distant-delta-xz6.bin']
provenance={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in files}
recipe=hashlib.sha256(''.join(provenance[n] for n in files).encode()).digest();choices=[]
for preset in (3,6):
 start=time.process_time();stream=lzma.compress(decoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=preset);assert lzma.decompress(stream)==decoded
 asset=folder/f'joint-transient-xz{preset}.bin';asset.write_bytes(b'TRJXZ001'+header[8:]+struct.pack('<QII',len(decoded),5,6)+recipe+stream)
 choices.append({'preset':preset,'asset_bytes':asset.stat().st_size,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'cpu_seconds':time.process_time()-start,'v90_64_total_bytes':95950504+asset.stat().st_size})
r={'architecture_only':True,'golden_labels_used':False,'anchor_bands':[70,96],'sources':160,'targets':160,'decoded_bytes':len(decoded),'nonzero_fraction':float((a!=0).mean()),'mean_absolute_delta_ps':float(np.abs(a.astype(np.int32)).mean()),'baseline_assets':provenance,'recipe_sha256':recipe.hex(),'choices':choices,'exact_roundtrip':True,'scope':'All-port nominal finite-graph interaction coefficients at one distance pair; no runtime integration, independent distance-band generalization, full validation or throughput evidence yet.'}
(ROOT/'reports/V91-joint-patch-feasibility.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
