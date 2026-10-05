"""Lossless stronger offline codec for distant replacement patch."""
import hashlib,json,lzma,time
from architecture import ROOT
source=ROOT/'out/architecture-benchmark/vertical-distant-delta-xz.bin';data=source.read_bytes();assert data[:8]==b'TRVFD002'
decoded=lzma.decompress(data[408:]);start=time.process_time();stream=lzma.compress(decoded,format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC32,preset=6);assert lzma.decompress(stream)==decoded
asset=ROOT/'out/architecture-benchmark/vertical-distant-delta-xz6.bin';asset.write_bytes(data[:408]+stream)
r={'source_bytes':len(data),'asset_bytes':asset.stat().st_size,'exact_roundtrip':True,'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'compression_cpu_seconds':time.process_time()-start,'v86_64_files_if_replacing_patch_bytes':97612812-12455824+asset.stat().st_size,'scope':'Offline lossless compression feasibility only, unchanged decoded architecture coefficients; no runtime validation or accuracy improvement.'}
(ROOT/'reports/V87-distant-xz6-feasibility.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
