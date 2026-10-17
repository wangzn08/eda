"""Measure lossless curve representations before allocating a full bank."""
import json,lzma,time,hashlib
import numpy as np
from architecture import ROOT
folder=ROOT/'out/v167';raw=(folder/'curves.raw.bin').read_bytes();header=raw[:432]
assert header[:8]==b'CURVRAW1';shape=np.frombuffer(header,dtype='<u4',offset=392,count=6);assert shape.tolist()==[4,160,239,24,48,2]
values=np.frombuffer(raw,dtype='<i2',offset=432).reshape(-1,48);start=time.monotonic();offsets=values[:,0].copy();wide=values.astype(np.int32)-offsets[:,None];assert wide.min()>=-32768 and wide.max()<=32767
normalized=wide.astype('<i2');del wide
patterns,codes=np.unique(normalized,axis=0,return_inverse=True);dtype='<u2' if len(patterns)<=65536 else '<u4';codes=codes.astype(dtype)
payload=offsets.astype('<i2').tobytes()+patterns.astype('<i2').tobytes()+codes.tobytes();compressed=lzma.compress(payload,preset=3);(folder/'curves.dictionary.xz').write_bytes(compressed)
decoded=lzma.decompress(compressed);assert decoded==payload
late=0;changes=0
for start_row in range(0,len(values),65536):
 stop=min(len(values),start_row+65536);part=values[start_row:stop]
 reconstructed=(patterns[codes[start_row:stop]].astype(np.int32)+offsets[start_row:stop,None]).astype('<i2');assert np.array_equal(reconstructed,part)
 change=np.diff(part.astype(np.int32),n=2,axis=1)!=0;late+=int(change[:,6:].any(axis=1).sum());changes+=int(change.sum())
r={'state':'complete','scope':'Four ideal-graph source cores only; whole-bank size and accuracy are unverified','source_indices':[0,53,106,159],'curves':len(values),'unique_normalized_curves':len(patterns),'index_bytes':codes.dtype.itemsize,'raw_bytes':len(raw),'dictionary_xz_bytes':len(compressed),'naive_40x_size_estimate_bytes':40*len(compressed),'naive_estimate_warning':'Not a guarantee: unseen sources may introduce new patterns and different compression ratios','roundtrip_exact':True,'raw_sha256':hashlib.sha256(raw).hexdigest(),'fraction_curves_with_slope_change_after_period6':late/len(values),'mean_slope_change_count':changes/len(values),'elapsed_seconds':time.monotonic()-start}
(ROOT/'reports/V167-response-curve-storage.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
