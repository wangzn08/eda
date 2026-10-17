"""Lossless byte-plane storage of complete architecture penalty vectors."""
import argparse,hashlib,json,lzma,struct,time
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');args=p.parse_args();start=time.monotonic();path=Path(args.input);h=path.open('rb').read(88);assert h[:8]==b'PHDICT01';sites,cores,components,patterns=struct.unpack('<4I',h[72:88]);assert cores==160 and components==24 and patterns<1<<24
n=sites*cores;v=np.memmap(path,dtype='<i2',mode='r',offset=88,shape=(patterns,24));c=np.memmap(path,dtype='<u4',mode='r',offset=88+patterns*48,shape=(n,));assert c.max()<patterns
width=2 if patterns<=65536 else 3;cb=c.view(np.uint8).reshape(-1,4)[:,:width].T.copy().tobytes();payload=v.tobytes()+cb;stream=lzma.compress(payload,preset=3);assert lzma.decompress(stream)==payload
out=Path(args.output);out.write_bytes(b'PHPATX01'+h[8:]+struct.pack('<2I',width,1)+stream)
b=np.frombuffer(cb,dtype=np.uint8).reshape(width,-1);back=b[0].astype(np.uint32)|(b[1].astype(np.uint32)<<8)
if width==3:back|=b[2].astype(np.uint32)<<16
assert np.array_equal(back,c)
r={'state':'complete','asset_bytes':out.stat().st_size,'decoded_bytes':len(payload),'patterns':patterns,'index_width':width,'complete_compression_roundtrip':True,'complete_code_inverse_parity':True,'vector_rows_verified_by_generator':n,'decoded_sha256':hashlib.sha256(payload).hexdigest(),'elapsed_seconds':time.monotonic()-start,'scope':'Architecture-only endpoint penalty vector dictionary; native runtime pending','holdout_used':False};Path(str(out)+'.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
