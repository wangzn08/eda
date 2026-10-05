"""Encode only extra deviations from current far model, not near model."""
import hashlib,json,lzma,struct,time
import numpy as np
from architecture import ROOT
folder=ROOT/'out/architecture-benchmark';shape=(160,160,59,2,2,12)
f=np.memmap(folder/'vertical-far.raw.bin',mode='r',dtype='<i2',offset=392,shape=shape);d=np.memmap(folder/'vertical-distant.raw.bin',mode='r',dtype='<i2',offset=392,shape=shape)
f5=f[:,:,:,:,1,:].astype(np.int32);s=np.maximum(0,f5-f[:,:,:,:,0,:].astype(np.int32));delta=d.astype(np.int32)
for band,q in enumerate((6,7)):delta[:,:,:,:,band,:]-=f5+(q-5)*s
assert delta.min()>=-32768 and delta.max()<=32767
encoded=delta.astype('<i2').tobytes();start=time.process_time();stream=lzma.compress(encoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=3);assert lzma.decompress(stream)==encoded
with (folder/'vertical-distant.raw.bin').open('rb') as file:header=file.read(392)
asset=folder/'vertical-distant-increment-xz.bin';asset.write_bytes(b'TRVFI001'+header[8:]+struct.pack('<IQI',0,len(encoded),6)+stream)
r={'architecture_only':True,'golden_labels_used':False,'nonzero_fraction':float((delta!=0).mean()),'asset_bytes':asset.stat().st_size,'exact_roundtrip':True,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'v86_64_files_plus_increment_bytes':97612812+asset.stat().st_size,'cpu_seconds':time.process_time()-start,'scope':'New third-band storage feasibility; current runtime cannot load TRVFI001. No validation or throughput claim.'}
(ROOT/'reports/V87-distant-increment-feasibility.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
