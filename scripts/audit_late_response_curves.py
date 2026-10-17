"""Lossless late-curve feasibility: omit early periods already covered by assets."""
import json,lzma,time,gc
import numpy as np
from architecture import ROOT
folder=ROOT/'out/v167';v=np.memmap(folder/'curves.raw.bin',dtype='<i2',mode='r',offset=432,shape=(4,160,239,24,48));start=time.monotonic();r={'state':'running','scope':'Four-source lossless feasibility only; naive40x projection is not a guarantee','cases':[]}
for name,xlo,xhi,first in [('all-late8',0,239,8),('near-late8',90,149,8),('all-late20',0,239,20)]:
 values=np.array(v[:,:,xlo:xhi,:,first:],copy=True).reshape(-1,48-first);offsets=values[:,0].copy();wide=values.astype(np.int32)-offsets[:,None];assert wide.min()>=-32768 and wide.max()<=32767;normalized=wide.astype('<i2');del wide
 patterns,codes=np.unique(normalized,axis=0,return_inverse=True);dtype='<u2' if len(patterns)<=65536 else '<u4';codes=codes.astype(dtype);payload=offsets.astype('<i2').tobytes()+patterns.astype('<i2').tobytes()+codes.tobytes();c=lzma.compress(payload,preset=3);assert lzma.decompress(c)==payload
 for i in range(0,len(values),65536):
  j=min(i+65536,len(values));assert np.array_equal((patterns[codes[i:j]].astype(np.int32)+offsets[i:j,None]).astype('<i2'),values[i:j])
 (folder/f'{name}.dictionary.xz').write_bytes(c);item={'name':name,'first_period':first,'curves':len(values),'unique_patterns':len(patterns),'xz_bytes':len(c),'naive40x_bytes':40*len(c),'roundtrip_exact':True,'elapsed_seconds':time.monotonic()-start};r['cases'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V167-late-curve-storage.json').write_text(json.dumps(r,indent=2)+'\n');del values,offsets,normalized,patterns,codes,payload,c;gc.collect()
r['state']='complete';(ROOT/'reports/V167-late-curve-storage.json').write_text(json.dumps(r,indent=2)+'\n')
