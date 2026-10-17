"""Streaming lossless compression and architecture-only parity checks."""
import argparse,hashlib,json,lzma,struct,time
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('field');p.add_argument('raw');p.add_argument('asset');p.add_argument('--planes',action='store_true');p.add_argument('--canonical',action='store_true');args=p.parse_args();start=time.monotonic()
path=Path(args.field);h=path.open('rb').read(670);assert h[:8]==b'FDSHORT1'
shape=struct.unpack('<8I',h[392:424]);assert shape==(160,160,119,24,8,2,1,0)
xs=np.frombuffer(h[424:662],dtype='<i2');minimum,maximum=struct.unpack('<2i',h[662:670]);n=160*119*24*8*160
v=np.memmap(path,dtype='<u2',mode='r',offset=670,shape=(n,));assert path.stat().st_size==670+n*2
flags=int(args.planes);compress=lzma.LZMACompressor(preset=3);original=hashlib.sha256()
out_count=n//8 if args.canonical else n
out_header=h if not args.canonical else h[:392]+struct.pack('<8I',20,160,119,24,8,2,0,0)+h[424:]
asset=Path(args.asset)
with asset.open('wb') as f:
    f.write(b'FDSHRT02'+out_header[8:]+struct.pack('<I',flags))
    for plane in (range(2) if args.planes else [None]):
        for i in range(0,n,2**20):
            values=v[i:i+2**20]
            if args.canonical:values=values.reshape(-1,8)[:,0]
            b=values.tobytes() if plane is None else ((values>>(8*plane))&255).astype(np.uint8).tobytes()
            original.update(b);f.write(compress.compress(b))
    f.write(compress.flush())
decoded=hashlib.sha256();decompress=lzma.LZMADecompressor();decoded_bytes=0
with asset.open('rb') as f:
    f.seek(674)
    while b:=f.read(1<<20):
        # Limit each decode allocation even when input has a very high ratio.
        result=decompress.decompress(b,max_length=1<<24)
        decoded.update(result);decoded_bytes+=len(result)
        while not decompress.needs_input and not decompress.eof:
            result=decompress.decompress(b'',max_length=1<<24);decoded.update(result);decoded_bytes+=len(result)
assert decompress.eof and decoded_bytes==out_count*2 and decoded.digest()==original.digest()
rng=np.random.default_rng(20261008);samples=200000;s=rng.integers(160,size=samples);t=rng.integers(160,size=samples);x=rng.integers(119,size=samples);y=rng.integers(24,size=samples);q=rng.integers(8,size=samples)
logical_s=s%20*8+s//20;logical_t=t%20*8+(t//20-s//20)%8
row=(((logical_t*119+x)*24+y)*8+q)*160+(logical_s//8)*8
z=v[row[:,None]+np.arange(8)].astype(np.int32);difference=(z>>1)^(-(z&1));values=difference.cumsum(axis=1)[np.arange(samples),s//20]
raw=np.memmap(args.raw,dtype='<i2',mode='r',offset=416,shape=(160,160,239,24,46));dx=xs[x].astype(np.int32);reference=np.sign(dx)*(20+np.abs(dx)%10)
expected=raw[s,t,dx+119,y,q].astype(np.int32);far=x>=59;expected[far]-=raw[s[far],t[far],reference[far]+119,y[far],q[far]]
assert np.array_equal(values,expected)
report={'state':'complete','asset_bytes':asset.stat().st_size,'decoded_bytes':decoded_bytes,'planes':args.planes,'canonical_source_count':20 if args.canonical else 160,'scalar_minimum':minimum,'scalar_maximum':maximum,'packed_bits':int(maximum-minimum).bit_length(),'compressed_roundtrip_sha256':original.hexdigest(),'raw_scalar_parity_samples':samples,'elapsed_seconds':time.monotonic()-start,'scope':'Architecture-only short vertical scalar bank, far horizontal samples 1/4/8; canonical mode approximates weighted lane rotation, standard runtime pending','holdout_used':False}
Path(str(asset)+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
