"""Lossless source gradients and byte planes for the full finite ideal bank."""
import argparse,json,lzma,struct,time
from pathlib import Path
import numpy as np
parser=argparse.ArgumentParser();parser.add_argument('dictionary');parser.add_argument('asset');parser.add_argument('--raw',required=True);parser.add_argument('--flags',type=int);args=parser.parse_args();path=Path(args.dictionary);start=time.monotonic()
with path.open('rb') as f:h=f.read(424)
assert h[:8]==b'FDCDICT2';sources,targets,nx,ny,first,nq,patterns,width=struct.unpack('<8I',h[392:424]);assert (targets,nx,ny,width)==(160,239,24,4);assert first+nq<=46 and patterns<1<<24
count=sources*targets*nx*ny
o=np.memmap(path,dtype='<i2',mode='r',offset=424,shape=(count//sources,sources))
p=np.memmap(path,dtype='<i2',mode='r',offset=424+count*2,shape=(patterns,nq))
c=np.memmap(path,dtype='<u4',mode='r',offset=424+count*2+patterns*nq*2,shape=(count,))
offsets=o.copy();difference=o[:,1:].astype(np.int32)-o[:,:-1].astype(np.int32);assert np.all((difference>=-32768)&(difference<=32767));offsets[:,1:]=difference
flags=args.flags if args.flags is not None else (39 if first==0 else 15)
assert flags&7==7 and (bool(flags&32)==(first==0))
ob=b'' if first==0 else offsets.reshape(-1).view(np.uint8).reshape(-1,2).T.copy().tobytes()
remap=None;original_pattern=p
if flags&256:
    order=np.argsort(p.view(np.dtype((np.void,nq*2))).reshape(-1),kind='stable')
    remap=np.empty(patterns,np.uint32);remap[order]=np.arange(patterns,dtype=np.uint32)
    original_pattern=p[order]
code=(c.copy() if remap is None else remap[c]).reshape(targets,nx,ny,sources)
if flags&16:code[:,:,:,1:]=(code[:,:,:,1:]-code[:,:,:,:-1])&0xffffff
if flags&128:code[:,10:,:,:]=(code[:,10:,:,:]-code[:,:-10,:,:])&0xffffff
pattern=original_pattern.copy()
if flags&64:
    dp=original_pattern[:,1:].astype(np.int32)-original_pattern[:,:-1].astype(np.int32);assert np.all((dp>=-32768)&(dp<=32767));pattern[:,1:]=dp
cb=code.reshape(-1).view(np.uint8).reshape(-1,4)[:,:3].T.copy().tobytes()
payload=ob+pattern.tobytes()+cb
compressed=lzma.compress(payload,preset=3);assert lzma.decompress(compressed)==payload
asset=b'FDCCURV2'+h[8:392]+struct.pack('<8I',sources,targets,nx,ny,first,nq,patterns,3)+struct.pack('<I',flags)+compressed
Path(args.asset).write_bytes(asset)
for i in range(0,len(o),4096):
    back=offsets[i:i+4096].astype(np.int32).cumsum(axis=1)
    assert np.array_equal(back,o[i:i+4096])
for target in range(targets):
    back=code[target].copy()
    if flags&128:
        for x in range(10,nx):back[x]=(back[x]+back[x-10])&0xffffff
    if flags&16:back=(back.astype(np.uint64).cumsum(axis=2)&0xffffff).astype(np.uint32)
    original=c.reshape(targets,nx,ny,sources)[target]
    assert np.array_equal(back,original if remap is None else remap[original])
if flags&64:assert np.array_equal(pattern.astype(np.int32).cumsum(axis=1),original_pattern)
raw=np.memmap(args.raw,dtype='<i2',mode='r',offset=416,shape=(160,160,239,24,46));rng=np.random.default_rng(20261008)
s=rng.integers(sources,size=100000);t=rng.integers(160,size=len(s));x=rng.integers(239,size=len(s));y=rng.integers(24,size=len(s));q=rng.integers(nq,size=len(s));row=(t*239+x)*24+y;pos=row*sources+s
sample_code=c[pos] if remap is None else remap[c[pos]]
assert np.array_equal(o[row,s].astype(np.int32)+original_pattern[sample_code,q],raw[s,t,x,y,q+first])
report={'state':'complete','source_count':sources,'period_first':first,'period_count':nq,'flags':flags,'shared_period8_offsets_omitted':first==0,'patterns':patterns,'asset_bytes':len(asset),'decoded_bytes':len(payload),'compression_payload_roundtrip_exact':True,'offset_transform_roundtrip_all':True,'code_transform_roundtrip_all':True,'pattern_transform_roundtrip_all':True,'raw_point_parity_samples':len(s),'elapsed_seconds':time.monotonic()-start,'scope':'Architecture-only lossless bank; complete submission and native query performance pending','holdout_used':False}
Path(args.asset+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
