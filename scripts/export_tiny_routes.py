"""Compile endpoint-phase factors and transpose dense layers for SIMD CPU loops."""
import argparse,hashlib,json,re,struct
from pathlib import Path
import numpy as np
import torch
from architecture import ROOT

def phase_table(state,prefix,routes):
    base=state['s.weight' if prefix=='s' else 't.weight'].numpy();factor=state['ps.weight' if prefix=='s' else 'pt.weight'].numpy()
    xx=state[prefix+'x'].numpy();yy=state[prefix+'y'].numpy()
    x=np.einsum('pk,xkr->pxr',factor,xx);y=np.einsum('pk,ykr->pyr',factor,yy)
    return (base[:,None,None,:]+x[:,:,None,:]+y[:,None,:,:]).reshape(496*120,routes).astype(np.float32)

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--phase-format',choices=['table','factor'],default='table');args=p.parse_args()
    model=torch.load(args.source,map_location='cpu',weights_only=False);state=model['state'];n,h,r=model['numeric'],model['hidden'],model['routes'];assert n==71 and h in (64,128) and r in (64,128)
    arch_hash=re.search(r'HASH\[\]="([0-9a-f]{64})"',(ROOT/'src/architecture_data.hpp').read_text())[1];tables=[phase_table(state,c,r) for c in ('s','t')];quant=[];scales=[]
    for table in tables:
        scale=max(float(np.max(np.abs(table)))/32760,1e-9);quant.append(np.rint(table/scale).astype('<i2'));scales.append(scale)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('wb') as f:
        f.write(b'TINYROU1' if args.phase_format=='table' else b'TINYROU2');f.write(arch_hash.encode());f.write(struct.pack('<3I',n,h,r));f.write(np.asarray(model['mean'],dtype='<f4').tobytes());f.write(np.asarray(model['std'],dtype='<f4').tobytes())
        for layer in (0,2,4):
            f.write(state[f'geo.{layer}.weight'].numpy().T.astype('<f4').tobytes());f.write(state[f'geo.{layer}.bias'].numpy().astype('<f4').tobytes())
        if args.phase_format=='table':
            for scale,q in zip(scales,quant):f.write(struct.pack('<f',scale));f.write(q.tobytes())
        else:
            for name in ('s.weight','t.weight','ps.weight','pt.weight','sx','sy','tx','ty'):f.write(state[name].numpy().astype('<f4').tobytes())
    report={'model':str(args.output),'source':str(args.source),'bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'architecture_sha256':arch_hash,'hidden':h,'routes':r,'phase_format':args.phase_format,'phase_table_scales':scales,'phase_table_max_abs_error':[float(np.max(np.abs(table-q.astype(np.float32)*np.float32(scale)))) for table,q,scale in zip(tables,quant,scales)],'phase_tables':'Learned endpoint factors evaluated over all 496 ports and 120 residues; not request-answer tables','runtime_scope':'Hard minimum; C++ validation still required'}
    args.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
