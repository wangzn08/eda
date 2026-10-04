"""Export source-column × port-family × direction residual coefficients."""
import json

from architecture import DEFAULT_ARCH, ROOT
from experiment_port_interaction import family
from experiment_region_port import load
from experiment_source_x_resolution import fit


def main():
    ports=json.loads((DEFAULT_ARCH/'SRB_Port.json').read_text())['Port']
    families=sorted({family(p['Name']) for p in ports})
    lookup={name:i for i,name in enumerate(families)}
    table=fit(load('development'),1,20)
    values=[0.0]*(len(families)*120*9)
    for (port,column,dx,dy),value in table.items():
        values[((lookup[port]*120+column)*3+dx+1)*3+dy+1]=value
    path=ROOT/'src/source_x_model.hpp'
    path.write_text('\n'.join([
        '// Generated from development labels and the frozen port-model output.',
        '#pragma once','#include <array>','namespace source_x_model {',
        f'constexpr std::array<double,{len(values)}> residual={{{",".join(format(x,".17g") for x in values)}}};',
        '} // namespace source_x_model','']))
    print(json.dumps({'path':str(path),'bytes':path.stat().st_size,
                      'nonzero_entries':len(table),'dense_entries':len(values)}))


if __name__=='__main__':main()
