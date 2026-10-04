"""Export fast V4 vertical-distance residual tables from development labels."""
import json

from architecture import Architecture,ROOT
from experiment_region_port import load
from experiment_v4_interactions import fit,key,score


def main():
    arch=Architecture()
    dev,val=load('development','v3-final'),load('validation','v3-final')
    specs=(('signed_dy_exact',1099*3),
           ('target_port_dy16',len(arch.ports)*35*3),
           ('source_port_dy16',len(arch.ports)*35*3))
    arrays=[];stages=[]
    for kind,length in specs:
        table=fit(dev,kind,20)
        values=[0.]*length
        for signature,value in table.items():
            if kind=='signed_dy_exact':
                dy,xsign=signature;index=(dy+549)*3+xsign+1
            else:
                port,bucket,ysign=signature
                index=(arch.port_ids[port]*35+bucket)*3+ysign+1
            values[index]=value
        def apply(rows):
            return [(*row[:7],max(0,round(row[7]+table.get(key(row,kind),0)))) for row in rows]
        dev=apply(dev);val=apply(val)
        arrays.append((kind,values))
        stages.append({'kind':kind,'nonzero_entries':len(table),'dense_entries':length,
                       'validation_score':score(val,kind,{})})
    path=ROOT/'src/v4_table_model.hpp'
    lines=['// Generated from development labels and frozen V3 predictions only.',
           '#pragma once','#include <array>','namespace v4_table_model {']
    for kind,values in arrays:
        lines.append(f'constexpr std::array<double,{len(values)}> {kind}={{{",".join(format(x,".17g") for x in values)}}};')
    lines.extend(['} // namespace v4_table_model',''])
    path.write_text('\n'.join(lines))
    report={'source':str(path),'bytes':path.stat().st_size,'stages':stages,
            'final_python_validation_score':stages[-1]['validation_score'],
            'holdout_used':False}
    (ROOT/'reports/V4-table-export.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
