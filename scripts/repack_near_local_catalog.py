"""Lossless target-local 16-bit curve ids and frequency ordering."""
import json,lzma,struct,time,hashlib
from pathlib import Path
import numpy as np
from architecture import ROOT
start=time.monotonic();source=ROOT/'out/v168/near-curves.bin';raw=source.read_bytes();h=raw[:424];assert h[:8]==b'CVNEAR01';npatt,width=struct.unpack('<2I',h[416:424]);assert width==4
n=160*160*59*24;decoded=lzma.decompress(raw[424:]);assert len(decoded)==n*6+npatt*80
offsets=np.frombuffer(decoded,dtype='<i2',count=n).reshape(160,160,59,24).transpose(1,2,3,0).copy()
patterns=np.frombuffer(decoded,dtype='<i2',count=npatt*40,offset=n*2).reshape(npatt,40)
codes=np.frombuffer(decoded,dtype='<u4',count=n,offset=n*2+npatt*80).reshape(160,160,59,24).transpose(1,2,3,0)
local=np.empty(codes.shape,dtype='<u2');maps=[];starts=[0]
for target in range(160):
    unique,inverse,counts=np.unique(codes[target].reshape(-1),return_inverse=True,return_counts=True);assert len(unique)<65536
    order=np.argsort(-counts,kind='stable');ranks=np.empty(len(unique),np.uint16);ranks[order]=np.arange(len(unique),dtype=np.uint16);local[target]=ranks[inverse].reshape(59,24,160);maps.append(unique[order].astype('<u4'));starts.append(starts[-1]+len(unique))
    assert np.array_equal(unique[order][local[target]],codes[target])
delta=offsets.copy();delta[:,:,:,1:]=(offsets[:,:,:,1:].astype(np.int32)-offsets[:,:,:,:-1]).astype('<i2');assert np.array_equal(delta.astype(np.int32).cumsum(axis=3),offsets)
catalog=np.concatenate(maps);prefix=np.array(starts,dtype='<u4');out=ROOT/'out/v210';out.mkdir(exist_ok=True)
report={'state':'running','scope':'Lossless architecture-only near late curves with per-target local ids; native implementation pending','holdout_used':False,'candidates':[]}
for flags in [15,31]:
    c=local.copy()
    if flags&16:c[:,:,:,1:]=(local[:,:,:,1:].astype(np.int32)-local[:,:,:,:-1]).astype('<u2')
    offsetbytes=delta.reshape(-1).view(np.uint8).reshape(-1,2).T.copy().tobytes();codebytes=c.reshape(-1).view(np.uint8).reshape(-1,2).T.copy().tobytes()
    payload=prefix.tobytes()+catalog.tobytes()+offsetbytes+patterns[:,:38].copy().tobytes()+codebytes
    stream=lzma.compress(payload,preset=3);assert lzma.decompress(stream)==payload
    header=b'CVNEAR03'+h[8:392]+struct.pack('<10I',160,160,59,24,38,8,npatt,2,flags,len(catalog))
    path=out/f'near-local-{flags}.bin';path.write_bytes(header+stream)
    back=c.astype(np.uint64).cumsum(axis=3).astype('<u2') if flags&16 else c
    assert np.array_equal(back,local)
    item={'flags':flags,'asset_bytes':path.stat().st_size,'decoded_bytes':len(payload),'local_catalog_ids':len(catalog),'maximum_target_catalog':max(np.diff(prefix)),'full_transform_parity':True,'full_compression_roundtrip':True,'decoded_sha256':hashlib.sha256(payload).hexdigest(),'elapsed_seconds':time.monotonic()-start};item['maximum_target_catalog']=int(item['maximum_target_catalog']);report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V210-near-local-catalog.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V210-near-local-catalog.json').write_text(json.dumps(report,indent=2)+'\n')
