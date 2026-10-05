"""Independent96..119 nominal bands vs near/far extrapolation; no request labels."""
import hashlib,json,lzma,struct,time
import numpy as np
from architecture import ROOT
folder=ROOT/'out/architecture-benchmark';raw=folder/'vertical-distant.raw.bin'
with raw.open('rb') as f:header=f.read(392)
assert header[:8]==b'TRANSVG1'
shape=(160,160,59,2,2,12)
arrays={n:np.memmap(folder/f'vertical-{n}.raw.bin',mode='r',dtype='<i2',offset=392,shape=shape) for n in ('transients','far','distant')}
items=[]
for sign,name in enumerate(('south','north')):
 a=arrays['transients'][:,:,:,sign,0,:].astype(np.int32);b=arrays['transients'][:,:,:,sign,1,:].astype(np.int32)
 f4=arrays['far'][:,:,:,sign,0,:].astype(np.int32);f5=arrays['far'][:,:,:,sign,1,:].astype(np.int32)
 for band,q in enumerate((6,7)):
  truth=arrays['distant'][:,:,:,sign,band,:].astype(np.int32)
  for method,p in [('near',b+(q-2)*np.maximum(0,b-a)),('far',f5+(q-5)*np.maximum(0,f5-f4))]:
   e=p-truth;items.append({'direction':name,'periods':q,'method':method,'entries':e.size,'mean_absolute_error_ps':float(np.abs(e).mean()),'p95_absolute_error_ps':float(np.quantile(np.abs(e),.95)),'exact_fraction':float((e==0).mean()),'mean_signed_error_ps':float(e.mean())})
near=arrays['transients'];far=arrays['far'];distant=arrays['distant']
old_slope=np.maximum(0,far[:,:,:,:,1,:].astype(np.int32)-far[:,:,:,:,0,:].astype(np.int32));new_slope=np.maximum(0,distant[:,:,:,:,1,:].astype(np.int32)-distant[:,:,:,:,0,:].astype(np.int32))
changed=float((new_slope!=old_slope).mean())
b=near[:,:,:,:,1,:].astype(np.int32);slope=np.maximum(0,b-near[:,:,:,:,0,:].astype(np.int32));delta=distant.astype(np.int32)
for band,q in enumerate((6,7)):delta[:,:,:,:,band,:]-=b+(q-2)*slope
assert delta.min()>=-32768 and delta.max()<=32767
start=time.process_time();encoded=delta.astype('<i2').tobytes();compressed=lzma.compress(encoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=3);assert lzma.decompress(compressed)==encoded
asset=folder/'vertical-distant-delta-xz.bin'
asset.write_bytes(b'TRVFD002'+header[8:]+struct.pack('<IQI',0,len(encoded),6)+compressed)
r={'architecture_only':True,'golden_labels_used':False,'bands':[96,108],'domain_radius':144,'cost_limit':5000,'recurrence_comparison':items,'growth_slope_change_fraction_from_far':changed,'asset_bytes':asset.stat().st_size,'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'exact_roundtrip':True,'compression_cpu_seconds':time.process_time()-start,'v86_64_files_if_replacing_patch_bytes':97612812-12455824+asset.stat().st_size,'scope':'Finite nominal architecture evidence, not physical route or validation improvement; TRVFD002 stores firstperiod6 and is not yet supported by runtime.'}
(ROOT/'reports/V87-distant-vertical-diagnosis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
