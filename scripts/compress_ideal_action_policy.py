"""Compress architecture shortest-path actions using shared source vectors.

Only a declared period coreset is kept; omitted periods use nearest anchors.
This is an approximation policy and must pass complete delay validation.
"""
import json,lzma,struct,time,hashlib
import numpy as np
from architecture import ROOT

folder=ROOT/'out/v189';path=folder/'actions.raw'
with path.open('rb') as f:
    h=f.read(416);assert h[:8]==b'ACTCURV1'
    shape=struct.unpack('<6I',h[392:416]);assert shape==(160,160,119,24,48,1)
    ids=f.read(640);assert np.array_equal(np.frombuffer(ids,'<u4'),np.arange(160))
    xs=f.read(476)
header_bytes=1532
assert path.stat().st_size==header_bytes+int(np.prod(shape[:5]))
raw=np.memmap(path,dtype='u1',mode='r',offset=header_bytes,shape=shape[:5])
knots=np.array([0,1,2,3,4,5,6,7,8,9,12,16,20,32,47],'<u4')
rowcount=160*119*24*len(knots);codes=np.empty(rowcount,'<u4')
dictionary={};patterns=[];start=time.monotonic()
for begin in range(0,rowcount,16384):
    end=min(begin+16384,rowcount);i=np.arange(begin,end);positions=(i//len(knots))*48+knots[i%len(knots)]
    matrix=np.stack([raw[s].reshape(-1)[positions] for s in range(160)],axis=1)
    unique,inverse=np.unique(np.ascontiguousarray(matrix).view('V160').reshape(-1),return_inverse=True)
    mapping=np.empty(len(unique),'<u4')
    for j,row in enumerate(unique):
        key=row.tobytes();p=dictionary.get(key)
        if p is None:
            p=len(patterns);dictionary[key]=p;patterns.append(key)
        mapping[j]=p
    codes[begin:end]=mapping[inverse]
    if begin%524288==0:print(json.dumps({'rows':end,'patterns':len(patterns),'elapsed':time.monotonic()-start}),flush=True)
    if len(patterns)>2500000:raise RuntimeError('Policy dictionary exceeds working storage budget; no asset published')
width=2 if len(patterns)<=65536 else 3
packed=np.column_stack([(codes>>(8*j)).astype('u1') for j in range(width)]).tobytes()
payload=b''.join(patterns)+packed
encoded=lzma.compress(payload,preset=6)
assert lzma.decompress(encoded)==payload
header=b'IACTPOL1'+h[8:72]+struct.pack('<6I',160,160,119,24,len(knots),width)+h[72:392]+xs+knots.tobytes()+struct.pack('<IQ',len(patterns),len(payload))
out=folder/'ideal-policy.bin';out.write_bytes(header+encoded)
report={'state':'complete','scope':'Full-source architecture action index, nearest q/dx anchors are approximate; native accuracy pending',
        'raw_bytes':path.stat().st_size,'policy_bytes':out.stat().st_size,'decoded_bytes':len(payload),'patterns':len(patterns),'width':width,
        'period_knots':knots.tolist(),'cpu_wall_seconds':time.monotonic()-start,'lossless_roundtrip_of_selected_anchors':True,
        'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'joint_goal_met':False}
(ROOT/'reports/V189-ideal-policy-storage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
