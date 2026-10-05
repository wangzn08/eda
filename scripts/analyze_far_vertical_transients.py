"""Compare independent nominal distance bands against near-band recurrence."""
import hashlib,json,lzma,struct,time
import numpy as np
from architecture import ROOT
folder=ROOT/'out/architecture-benchmark';raw=folder/'vertical-far.raw.bin'
with raw.open('rb') as f:header=f.read(392)
assert header[:8]==b'TRANSVF1'
shape=(160,160,59,2,2,12)
far=np.memmap(raw,mode='r',dtype='<i2',offset=392,shape=shape)
near=np.memmap(folder/'vertical-transients.raw.bin',mode='r',dtype='<i2',offset=392,shape=shape)
items=[]
for sign,name in enumerate(('south','north')):
 a=near[:,:,:,sign,0,:].astype(np.int32);b=near[:,:,:,sign,1,:].astype(np.int32);s=np.maximum(0,b-a)
 for band,q in enumerate((4,5)):
  truth=far[:,:,:,sign,band,:].astype(np.int32);err=b+(q-2)*s-truth
  items.append({'direction':name,'periods':q,'entries':err.size,'mean_absolute_error_ps':float(np.abs(err).mean()),'p95_absolute_error_ps':float(np.quantile(np.abs(err),.95)),'exact_fraction':float((err==0).mean()),'mean_signed_error_ps':float(err.mean())})
 fs=far[:,:,:,:,1,:].astype(np.int32)-far[:,:,:,:,0,:].astype(np.int32)
 ns=near[:,:,:,:,1,:].astype(np.int32)-near[:,:,:,:,0,:].astype(np.int32)
start=time.process_time();decoded=far.tobytes();stream=lzma.compress(decoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=3);assert lzma.decompress(stream)==decoded
asset=folder/'vertical-far-xz.bin';asset.write_bytes(b'TRVFX001'+header[8:]+struct.pack('<IQ',0,len(decoded))+stream)
r={'architecture_only':True,'golden_labels_used':False,'bands':[72,84],'residues':12,'recurrence_comparison':items,'growth_slope_change_fraction':float((np.maximum(0,fs)!=np.maximum(0,ns)).mean()),'asset_bytes':asset.stat().st_size,'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'exact_compression_roundtrip':True,'compression_cpu_seconds':time.process_time()-start,'scope':'Finite nominal graph diagnostic, not physical path certificate, full validation or query throughput.'}
# Store only discrepancy from the existing near recurrence, preserving exact far bands.
a=near[:,:,:,:,0,:].astype(np.int32);b=near[:,:,:,:,1,:].astype(np.int32);slope=np.maximum(0,b-a)
delta=far.astype(np.int32)
for band,q in enumerate((4,5)):delta[:,:,:,:,band,:]-=b+(q-2)*slope
assert delta.min()>=-32768 and delta.max()<=32767
encoded=delta.astype('<i2').tobytes();compressed=lzma.compress(encoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=3)
assert lzma.decompress(compressed)==encoded
patch=folder/'vertical-far-delta-xz.bin';patch.write_bytes(b'TRVFD001'+header[8:]+struct.pack('<IQ',0,len(encoded))+compressed)
r['delta_asset_bytes']=patch.stat().st_size;r['delta_exact_roundtrip']=True;r['delta_asset_sha256']=hashlib.sha256(patch.read_bytes()).hexdigest()
r['v82_128_files_plus_delta_bytes']=85685772+patch.stat().st_size
(ROOT/'reports/V83-far-vertical-diagnosis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
