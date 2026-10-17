"""Pilot storage for architecture-derived first-action response curves."""
import json,lzma,struct,time
import numpy as np
from architecture import ROOT,Architecture

p=ROOT/'out/v188/actions.raw';header=p.read_bytes()[:828]
assert header[:8]==b'ACTCURV1';shape=struct.unpack('<6I',header[392:416])
assert shape==(4,160,99,24,48,1)
ids=np.frombuffer(header,dtype='<u4',count=4,offset=416)
data=np.memmap(p,mode='r',dtype=np.uint8,offset=828,shape=shape[:5])
begin=time.monotonic();report={'scope':'Four-source ideal action storage pilot, full-source projections are not measurements','shape':shape,'candidates':[]}
for name,values in [('net_ids',data)]:
    curves=values.reshape(-1,48)
    packed=curves.view('V48').reshape(-1)
    patterns,codes=np.unique(packed,return_inverse=True)
    width=2 if len(patterns)<=65536 else 4
    codebytes=codes.astype('<u2' if width==2 else '<u4').tobytes()
    payload=patterns.tobytes()+codebytes
    encoded=lzma.compress(payload,preset=6)
    assert lzma.decompress(encoded)==payload
    assert np.array_equal(patterns[codes].view(np.uint8).reshape(curves.shape),curves)
    (p.parent/f'{name}.xz').write_bytes(encoded)
    item={'name':name,'patterns':len(patterns),'xz_bytes':len(encoded),'naive_160_source_projection_bytes':40*len(encoded),'constant_after_q20_fraction':float(np.mean(np.all(curves[:,20:]==curves[:,20,None],axis=1))),'lossless_roundtrip':True,'elapsed_seconds':time.monotonic()-begin}
    report['candidates'].append(item);print(json.dumps(item),flush=True)
(ROOT/'reports/V188-ideal-action-storage.json').write_text(json.dumps(report,indent=2)+'\n')
