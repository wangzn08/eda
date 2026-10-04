"""Export target-column × port-family × direction residual coefficients."""
import json

from architecture import DEFAULT_ARCH, ROOT
from experiment_after_source_x import fit
from experiment_port_interaction import family
from experiment_region_port import load


def main():
    ports=json.loads((DEFAULT_ARCH/'SRB_Port.json').read_text())['Port']
    families=sorted({family(p['Name']) for p in ports})
    lookup={name:i for i,name in enumerate(families)}
    table=fit(load('development','source-x'),'target_x_family_dir',20)
    values=[0.0]*(len(families)*120*9)
    for (port,column,dx,dy),value in table.items():
        values[((lookup[port]*120+column)*3+dx+1)*3+dy+1]=value
    path=ROOT/'src/target_x_model.hpp'
    path.write_text('\n'.join([
        '// Generated from development labels and source-x-model predictions.',
        '#pragma once','#include <array>','namespace target_x_model {',
        f'constexpr std::array<double,{len(values)}> residual={{{",".join(format(x,".17g") for x in values)}}};',
        '} // namespace target_x_model','']))
    print(json.dumps({'path':str(path),'bytes':path.stat().st_size,
                      'nonzero_entries':len(table),'dense_entries':len(values)}))


if __name__=='__main__':main()
