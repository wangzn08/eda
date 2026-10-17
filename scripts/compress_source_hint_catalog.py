"""Reversible per-source catalogs for the architecture source selection masks."""
import argparse,hashlib,json,lzma,struct,time
from pathlib import Path
import numpy as np
from architecture import Architecture
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');args=p.parse_args();start=time.monotonic();raw=Path(args.input).read_bytes();assert raw[:8]==b'SRCMSK01';count,size=struct.unpack('<IQ',raw[72:84]);assert count==8
data=lzma.decompress(raw[84:]);assert len(data)==size
arch=Architecture();core={n['to'] for n in arch.nets};out_ports={n['from'] for n in arch.nets};entry={p['Name']:0 for p in arch.ports};terminal=core.copy()
for arc in arch.arcs:
    if arc['to'] in out_ports:entry[arc['from']]+=1
    if arc['from'] in core:terminal.add(arc['to'])
sources=sum(p not in core|out_ports and n>16 for p,n in entry.items());targets=len(terminal);phases=1896;a=np.frombuffer(data,dtype='<u4').reshape(sources,targets*phases);code=np.empty(a.shape,dtype='<u2');catalog=[];starts=[0]
for source in range(sources):
    unique,inverse=np.unique(a[source],return_inverse=True);assert len(unique)<=65536;code[source]=inverse;catalog.append(unique);starts.append(starts[-1]+len(unique));assert np.array_equal(unique[code[source]],a[source])
prefix=np.array(starts,dtype='<u4');values=np.concatenate(catalog).astype('<u4');cb=code.reshape(-1).view(np.uint8).reshape(-1,2).T.copy().tobytes();payload=prefix.tobytes()+values.tobytes()+cb;stream=lzma.compress(payload,preset=3);assert lzma.decompress(stream)==payload
out=Path(args.output);out.write_bytes(b'SRCLOC01'+raw[8:72]+struct.pack('<6I',sources,targets,phases,count,len(values),2)+stream)
wire=np.frombuffer(cb,dtype=np.uint8).reshape(2,-1);back=(wire[0].astype(np.uint16)|(wire[1].astype(np.uint16)<<8)).reshape(a.shape);assert np.array_equal(back,code)
r={'state':'complete','asset_bytes':out.stat().st_size,'decoded_bytes':len(payload),'original_decoded_bytes':size,'catalog_masks':len(values),'maximum_source_catalog':int(np.diff(prefix).max()),'all_mask_memberships_preserved':True,'complete_code_inverse_parity':True,'complete_compressed_roundtrip':True,'decoded_sha256':hashlib.sha256(payload).hexdigest(),'elapsed_seconds':time.monotonic()-start,'scope':'Architecture-only lossless source hint storage, no candidate policy change','holdout_used':False};Path(str(out)+'.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
