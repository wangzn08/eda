"""Block dictionaries for ideal actions; bounded working memory, no golden data."""
import json,lzma,struct,time,hashlib
import numpy as np
from architecture import ROOT
folder=ROOT/'out/v189';path=folder/'actions.raw'
with path.open('rb') as f:
    h=f.read(416);assert h[:8]==b'ACTCURV1'
    assert struct.unpack('<6I',h[392:416])==(160,160,119,24,48,1)
    assert np.array_equal(np.frombuffer(f.read(640),'<u4'),np.arange(160))
    xs=f.read(476)
raw=np.memmap(path,dtype='u1',mode='r',offset=1532,shape=(160,160,119,24,48))
knots=np.array([0,1,2,3,4,5,6,7,8,9,12,16,20,32,47],'<u4');q=len(knots)
rows=160*119*24*q;i=np.arange(rows);positions=(i//q)*48+knots[i%q]
out=folder/'ideal-policy.block-partial';start=time.monotonic();blocks=[];decoded_total=0
with out.open('wb') as f:
    f.write(b'IACTPOL2'+h[8:72]+struct.pack('<6I',160,160,119,24,q,8)+h[72:392]+xs+knots.tobytes()+struct.pack('<I',20))
    for block in range(20):
        matrix=np.ascontiguousarray(raw[block*8:block*8+8].reshape(8,-1)[:,positions].T)
        patterns,codes=np.unique(matrix.view('V8').reshape(-1),return_inverse=True)
        width=2 if len(patterns)<=65536 else 3;mask=(1<<(8*width))-1
        original=codes.astype('<u4').reshape(-1,q);delta=original.copy()
        delta[:,1:]=(original[:,1:]-original[:,:-1])&mask
        assert np.array_equal(np.cumsum(delta.astype(np.uint64),axis=1)&mask,original)
        packed=np.column_stack([(delta.reshape(-1)>>(8*j)).astype('u1') for j in range(width)]).tobytes()
        payload=patterns.tobytes()+packed;encoded=lzma.compress(payload,preset=6)
        assert lzma.decompress(encoded)==payload
        f.write(struct.pack('<IIQQ',len(patterns),width,len(payload),len(encoded)));f.write(encoded)
        decoded_total+=len(payload);item={'block':block,'patterns':len(patterns),'width':width,'decoded_bytes':len(payload),'xz_bytes':len(encoded),'elapsed_seconds':time.monotonic()-start};blocks.append(item);print(json.dumps(item),flush=True)
        del matrix,patterns,codes,original,delta,packed,payload,encoded
out.rename(folder/'ideal-policy.bin')
p=folder/'ideal-policy.bin';report={'state':'complete','scope':'All sources in eight-source action dictionaries; nearest period/x anchors approximate, native accuracy pending','blocks':blocks,'raw_bytes':path.stat().st_size,'policy_bytes':p.stat().st_size,'decoded_bytes':decoded_total,'knots':knots.tolist(),'lossless_roundtrip_of_selected_anchors':True,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'joint_goal_met':False}
(ROOT/'reports/V189-block-policy-storage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'state':'complete','bytes':p.stat().st_size,'decoded_bytes':decoded_total}),flush=True)
