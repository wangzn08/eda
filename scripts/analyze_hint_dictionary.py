"""Exact dictionary coding of architecture-only source-selection masks."""
import json,lzma,time,hashlib
import numpy as np
from architecture import ROOT
raw=(ROOT/'out/v109/source-hints.raw').read_bytes();assert raw[:8]==b'SRCMSK01';v=np.frombuffer(raw[84:],dtype='<u4');start=time.process_time();unique,indices=np.unique(v,return_inverse=True);bits=int(np.ceil(np.log2(len(unique))));width=2 if len(unique)<=65536 else 4;codes=indices.astype('<u2' if width==2 else '<u4');out=ROOT/'out/v143';out.mkdir(exist_ok=True)
stream=lzma.compress(codes.tobytes(),preset=6,check=lzma.CHECK_CRC32);roundtrip=np.frombuffer(lzma.decompress(stream),dtype=codes.dtype);assert np.array_equal(unique[roundtrip],v)
asset=raw[:84]+len(unique).to_bytes(4,'little')+width.to_bytes(4,'little')+unique.astype('<u4').tobytes()+stream;(out/'source-dictionary.research.bin').write_bytes(asset)
r={'state':'complete','unique_masks':len(unique),'bits_required':bits,'code_bytes':width,'asset_bytes':len(asset),'old_asset_bytes':(ROOT/'out/phase-fast15-v111/source-hints.bin').stat().st_size,'lossless_roundtrip':True,'decoded_sha256':hashlib.sha256(raw[84:]).hexdigest(),'cpu_seconds':time.process_time()-start,'scope':'architecture-only storage research; runtime decoder pending'};(ROOT/'reports/V143-source-hint-dictionary.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
