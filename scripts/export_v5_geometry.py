"""Export five geometry residual tables fitted after frozen V4 predictions."""
import json

from architecture import Architecture,ROOT
from experiment_region_port import load
from experiment_v4_interactions import fit,key,score


def index(kind,signature,arch):
    if kind=='source_x_target_x':
        sx,tx=signature;return sx*120+tx
    if kind=='source_port_x':
        port,sx=signature;return arch.port_ids[port]*120+sx
    if kind in ('source_yphase_dx16','target_yphase_dx16'):
        phase,bucket,sign=signature;return (phase*8+bucket)*3+sign+1
    if kind=='target_x_dx16':
        tx,bucket,sign=signature;return (tx*8+bucket)*3+sign+1
    raise ValueError(kind)


def main():
    arch=Architecture()
    dev,val=load('development','v4-horizontal'),load('validation','v4-horizontal')
    specs=(('source_x_target_x',120*120),
           ('source_port_x',len(arch.ports)*120),
           ('source_yphase_dx16',20*8*3),
           ('target_yphase_dx16',20*8*3),
           ('target_x_dx16',120*8*3))
    arrays=[];stages=[]
    for kind,length in specs:
        table=fit(dev,kind,20)
        values=[0.]*length
        for signature,value in table.items():values[index(kind,signature,arch)]=value
        def apply(rows):
            return [(*row[:7],max(0,round(row[7]+table.get(key(row,kind),0)))) for row in rows]
        dev,val=apply(dev),apply(val)
        arrays.append((kind,values))
        stages.append({'kind':kind,'nonzero_entries':len(table),'dense_entries':length,
                       'validation_score':score(val,kind,{})})
    path=ROOT/'src/v5_geometry_model.hpp'
    lines=['// Generated from development labels and frozen V4 predictions only.',
           '#pragma once','#include <array>','namespace v5_geometry_model {']
    for kind,values in arrays:
        lines.append(f'constexpr std::array<double,{len(values)}> {kind}={{{",".join(format(x,".17g") for x in values)}}};')
    lines.extend(['} // namespace v5_geometry_model',''])
    path.write_text('\n'.join(lines))
    report={'source':str(path),'bytes':path.stat().st_size,'stages':stages,
            'final_python_validation_score':stages[-1]['validation_score'],'holdout_used':False}
    (ROOT/'reports/V5-geometry-export.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
