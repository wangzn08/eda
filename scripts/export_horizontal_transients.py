"""Lossless export of architecture-only horizontal residual table."""
import hashlib,json,lzma,struct,time
from architecture import ROOT
raw=(ROOT/'out/architecture-benchmark/horizontal-transients.raw.bin').read_bytes();assert raw[:8]==b'TRANSH01';decoded=raw[392:];assert len(decoded)==160*160*71*40*2
start=time.process_time();stream=lzma.compress(decoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=3);assert lzma.decompress(stream)==decoded
asset=ROOT/'out/architecture-benchmark/horizontal-transients.bin';asset.write_bytes(b'TRHXZ001'+raw[8:392]+struct.pack('<IQ',0,len(decoded))+stream)
r={'architecture_only':True,'golden_labels_used':False,'decoded_values':len(decoded)//2,'asset_bytes':asset.stat().st_size,'exact_roundtrip':True,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'cpu_seconds':time.process_time()-start,'combined_with_v80_bytes':asset.stat().st_size+79497732,'scope':'Codec feasibility; horizontal/vertical coupling validation and full profile limits remain to evaluate.'}
(ROOT/'reports/V81-horizontal-export.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
