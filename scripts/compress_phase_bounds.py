"""Lossless dictionary compression of architecture-only phase lower bounds."""
import hashlib,json,struct,time
from pathlib import Path
import numpy as np
from architecture import ROOT

def main():
    source=ROOT/'out/architecture-benchmark/phase-bounds.raw.bin';target=ROOT/'out/architecture-benchmark/phase-bounds.dictionary.bin';begin=time.monotonic()
    with source.open('rb') as f:
        assert f.read(8)==b'PHASELB1';header=struct.unpack('<7I',f.read(28));version,p,ni,k,px1,px2,py=header;ports=f.read(2*ni);raw=np.frombuffer(f.read(),dtype='<i2')
    assert version==1 and k==4 and p==496 and ni==160
    reports=[];offset=0
    with target.open('wb') as f:
        f.write(b'PHASELD2');f.write(struct.pack('<7I',*header));f.write(ports)
        for px in [px1,px2]:
            phases=px*py;count=k*p*ni;matrix=raw[offset:offset+count*phases].reshape(count,phases);offset+=count*phases
            base=matrix.min(axis=1).astype('<i2');normalized=matrix.astype(np.int32)-base[:,None];assert normalized.max()<=65535;normalized=normalized.astype('<u2');palette,inverse=np.unique(normalized,axis=0,return_inverse=True);width=2 if len(palette)<=65536 else 4;indices=inverse.astype('<u2' if width==2 else '<u4')
            f.write(struct.pack('<3I',px,len(palette),width));f.write(base.tobytes());f.write(indices.tobytes());f.write(palette.astype('<u2').tobytes())
            assert np.array_equal(palette[indices].astype(np.int32)+base[:,None],matrix)
            reports.append({'x_period':px,'patterns':len(palette),'base_bytes':base.nbytes,'index_bytes':indices.nbytes,'pattern_bytes':palette.nbytes,'exact_roundtrip':True})
    assert offset==len(raw)
    report={'architecture_only':True,'golden_used':False,'source_bytes':source.stat().st_size,'compressed_bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'groups':reports,'seconds':time.monotonic()-begin}
    (ROOT/'reports/V38-phase-bound-compression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
