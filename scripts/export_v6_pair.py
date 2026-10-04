"""Export the score-aware source-port by target-port residual table."""
import json

from architecture import Architecture,ROOT
from experiment_region_port import load
from experiment_v6_pair_loss import fit_weighted
from experiment_v6_port_pair import score


def main():
    arch=Architecture()
    dev,val=load('development','v5-geometry-fused'),load('validation','v5-geometry-fused')
    table=fit_weighted(dev,alpha=.5,prior=1,cap=3)
    ports=len(arch.ports)
    values=[0.]*(ports*ports)
    for (source,target),correction in table.items():
        values[arch.port_ids[source]*ports+arch.port_ids[target]]=correction
    path=ROOT/'src/v6_pair_model.hpp'
    lines=['// Generated from development residuals of frozen V5 geometry predictions.',
           '#pragma once','#include <array>','namespace v6_pair_model {',
           f'constexpr std::array<double,{len(values)}> correction={{{",".join(format(x,".17g") for x in values)}}};',
           '} // namespace v6_pair_model','']
    path.write_text('\n'.join(lines))
    report={'source':str(path),'bytes':path.stat().st_size,
            'dense_entries':len(values),'nonzero_entries':len(table),
            'fit':{'alpha':.5,'prior':1,'cap':3},
            'python_validation_score':score(val,'pair',table),
            'holdout_used':False}
    (ROOT/'reports/V6-pair-export.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
