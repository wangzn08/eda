"""Architecture-only far curve dictionary with reversible source differences."""
import argparse,json,lzma,struct,time,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('dictionary');p.add_argument('raw');p.add_argument('asset');args=p.parse_args();start=time.monotonic();path=Path(args.dictionary)
with path.open('rb') as f:
    h=f.read(428);assert h[:8]==b'FDXDICT2';s,t,nx,ny,first,nq,npatt,width=struct.unpack('<8I',h[392:424]);na=struct.unpack('<I',h[424:428])[0];tail=f.read(na*4+nx*2)
assert (s,t,ny,first,nq,width)==(160,160,24,8,38,4);assert npatt<1<<24
anchors=np.frombuffer(tail,dtype='<u4',count=na);xs=np.frombuffer(tail,dtype='<i2',offset=na*4);header=h+tail;begin=len(header);n=s*t*nx*ny
offsets=np.memmap(path,dtype='<i2',mode='r',offset=begin,shape=(t,nx,ny,s));patterns=np.memmap(path,dtype='<i2',mode='r',offset=begin+n*2,shape=(npatt,nq));codes=np.memmap(path,dtype='<u4',mode='r',offset=begin+n*2+npatt*nq*2,shape=(n,))
delta=offsets.copy();delta[:,:,:,1:]=(offsets[:,:,:,1:].astype(np.int32)-offsets[:,:,:,:-1]).astype('<i2');assert np.array_equal(delta.astype(np.int32).cumsum(axis=3),offsets)
ob=delta.reshape(-1).view(np.uint8).reshape(-1,2).T.copy().tobytes();cb=codes.view(np.uint8).reshape(-1,4)[:,:3].T.copy().tobytes();payload=ob+patterns.tobytes()+cb
stream=lzma.compress(payload,preset=3);assert lzma.decompress(stream)==payload
asset=Path(args.asset);asset.write_bytes(b'FARABS01'+header[8:]+struct.pack('<I',15)+stream)
back=np.frombuffer(cb,dtype=np.uint8).reshape(3,-1);ids=back[0].astype(np.uint32)|(back[1].astype(np.uint32)<<8)|(back[2].astype(np.uint32)<<16);assert np.array_equal(ids,codes)
raw=np.memmap(args.raw,dtype='<i2',mode='r',offset=416,shape=(160,160,239,24,46));rng=np.random.default_rng(20261008);samples=200000;si=rng.integers(160,size=samples);ti=rng.integers(160,size=samples);xi=rng.integers(nx,size=samples);y=rng.integers(24,size=samples);q=rng.integers(38,size=samples);row=(((ti*nx+xi)*24+y)*160+si)
assert np.array_equal(offsets[ti,xi,y,si].astype(np.int32)+patterns[codes[row],q],raw[si,ti,xs[xi]+119,y,q+8])
report={'state':'complete','asset_bytes':asset.stat().st_size,'decoded_bytes':len(payload),'patterns':npatt,'anchors':anchors.tolist(),'complete_compressed_roundtrip':True,'complete_offset_inverse_parity':True,'complete_code_inverse_parity':True,'raw_point_parity_samples':samples,'decoded_sha256':hashlib.sha256(payload).hexdigest(),'elapsed_seconds':time.monotonic()-start,'scope':'Absolute ideal finite far kernel; source-adjacent compressed layout, native geometry/target layout pending','holdout_used':False}
Path(str(asset)+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
