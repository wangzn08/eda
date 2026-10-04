"""Export signed-horizontal-displacement residual after the two column terms."""
import json

from architecture import ROOT
from experiment_region_port import load
from experiment_xpair_detail import fit


def main():
    table=fit(load('development','target-x'),'exact_signed_displacement',20)
    values=[0.0]*(239*3)
    for (dx,ysign),value in table.items():
        values[(dx+119)*3+ysign+1]=value
    path=ROOT/'src/dx_model.hpp'
    path.write_text('\n'.join([
        '// Generated from development labels and target-x-model predictions.',
        '#pragma once','#include <array>','namespace dx_model {',
        f'constexpr std::array<double,{len(values)}> residual={{{",".join(format(x,".17g") for x in values)}}};',
        '} // namespace dx_model','']))
    print(json.dumps({'path':str(path),'bytes':path.stat().st_size,
                      'nonzero_entries':len(table),'dense_entries':len(values)}))


if __name__=='__main__':main()
