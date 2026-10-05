"""Lossless XZ variant for existing architecture transient residuals."""
import hashlib,json,lzma,time,zlib
from architecture import ROOT
source=ROOT/'out/architecture-benchmark/vertical-transients.bin';payload=source.read_bytes();decoded=zlib.decompress(payload[404:]);start=time.process_time()
stream=lzma.compress(decoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=3);assert lzma.decompress(stream)==decoded
asset=ROOT/'out/architecture-benchmark/vertical-transients-xz.bin';asset.write_bytes(b'TRVXZ001'+payload[8:404]+stream)
r={'architecture_only':True,'source_bytes':source.stat().st_size,'asset_bytes':asset.stat().st_size,'exact_roundtrip':True,'decoded_sha256':hashlib.sha256(decoded).hexdigest(),'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'cpu_seconds':time.process_time()-start,'scope':'Lossless residual codec only; no changed prediction or billion acceptance.'}
(ROOT/'reports/V80-vertical-xz-export.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
