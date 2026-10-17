"""Lossless serialization of architecture-only hint indices, preserving original assets."""
import hashlib,json,lzma,shutil,time
from pathlib import Path
from architecture import ROOT
folder=ROOT/'out/phase-fast15-v111';folder.mkdir(exist_ok=True);report={'architecture_only':True,'fit_labels_used':False,'holdout_used':False,'prediction_cache':False,'assets':{}}
for p in (ROOT/'out/phase-fast30-v108').glob('*.bin'):shutil.copyfile(p,folder/p.name)
for name in ['source-hints','horizontal-hints']:
 p=ROOT/f'out/v109/{name}.raw';data=p.read_bytes();header=data[:84];raw=data[84:];start=time.process_time();stream=lzma.compress(raw,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=6);assert lzma.decompress(stream)==raw
 q=folder/(name+'.bin');q.write_bytes(header+stream);item={'raw_bytes':len(raw),'file_bytes':q.stat().st_size,'decoded_sha256':hashlib.sha256(raw).hexdigest(),'compression_cpu_seconds':time.process_time()-start};report['assets'][q.name]=item;print(json.dumps({q.name:item}),flush=True)
# Recompress only the lossless transformed payload; finite-template values stay identical.
p=folder/'core-template.bin';data=p.read_bytes();raw=lzma.decompress(data[400:]);start=time.process_time();stream=lzma.compress(raw,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=9);assert lzma.decompress(stream)==raw;p.write_bytes(data[:400]+stream);report['assets'][p.name]={'old_bytes':len(data),'file_bytes':p.stat().st_size,'decoded_sha256':hashlib.sha256(raw).hexdigest(),'exact_roundtrip':True,'compression_cpu_seconds':time.process_time()-start};print(json.dumps({p.name:report['assets'][p.name]}),flush=True)
report['total_asset_bytes']=sum(p.stat().st_size for p in folder.glob('*.bin'));report['remaining_executable_budget_bytes']=100000000-report['total_asset_bytes'];(ROOT/'reports/V111-fast15-asset-compression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'total_asset_bytes':report['total_asset_bytes'],'remaining_executable_budget_bytes':report['remaining_executable_budget_bytes']}),flush=True)
