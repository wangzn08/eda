"""Lossless spatial first differences of architecture-derived portal legs."""
from pathlib import Path
import lzma,hashlib,json,time
import numpy as np
from architecture import ROOT
p=ROOT/'out/v140/portal.raw.bin';raw=p.read_bytes();assert len(raw)==111258032
start=time.process_time();v=np.frombuffer(raw[432:],dtype='<u2');n=106*50*160*16
parts=[]
for values,ports in [(v[:n],160),(v[n:],496)]:
 a=values.reshape(106,50,ports,16).copy()
 # Modulo arithmetic preserves sentinel and all uint16 values exactly.
 a[:,1:]=a[:,1:]-a[:,:-1]
 a[1:]=a[1:]-a[:-1]
 parts.append(a.tobytes())
encoded=lzma.compress(b''.join(parts),preset=6)
f=ROOT/'out/v140/portal.spatial.xz';f.write_bytes(raw[:432]+encoded)
b=np.frombuffer(lzma.decompress(encoded),dtype='<u2');decoded=[]
for values,ports in [(b[:n],160),(b[n:],496)]:
 a=values.reshape(106,50,ports,16).copy()
 a=np.cumsum(a,axis=0,dtype=np.uint64).astype('<u2');a=np.cumsum(a,axis=1,dtype=np.uint64).astype('<u2');decoded.append(a.tobytes())
assert b''.join(decoded)==raw[432:]
report={'state':'complete','bytes':f.stat().st_size,'lossless_roundtrip':True,'raw_sha256':hashlib.sha256(raw).hexdigest(),'asset_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'cpu_seconds':time.process_time()-start,'reachable_leg_max':int(v[v!=65535].max()),'unreachable_fraction':float(np.mean(v==65535)),'submission_ready':False}
(ROOT/'reports/V140-portal-compression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
