"""Lossless alternative core residual codec feasibility; no request labels."""
import hashlib,json,lzma,time,zlib
from architecture import ROOT
source=ROOT/'out/architecture-benchmark/core-template-zlib.bin';payload=source.read_bytes();decoded=zlib.decompress(payload[400:]);assert len(decoded)==214476800
start=time.process_time();stream=lzma.compress(decoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=3)
assert lzma.decompress(stream)==decoded
out=ROOT/'out/architecture-benchmark/core-template-xz.bin';out.write_bytes(b'COREXZ01'+payload[8:400]+stream)
r={'architecture_only':True,'codec':'XZ/LZMA2 preset3 CRC32','asset_bytes':out.stat().st_size,'source_asset_bytes':source.stat().st_size,
   'exact_roundtrip':True,'decoded_sha256':hashlib.sha256(decoded).hexdigest(),'asset_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
   'cpu_seconds':time.process_time()-start,'combined_transient_and_binary_bytes':out.stat().st_size+(ROOT/'out/architecture-benchmark/vertical-transients.bin').stat().st_size+(ROOT/'build/core_template_estimate').stat().st_size,
   'scope':'Compression feasibility only; C++decoder/dependency availability and final runtime packaging not validated.'}
(ROOT/'reports/V77-core-xz-feasibility.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2),flush=True)
