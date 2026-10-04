"""Export the validated port-family × direction correction table."""
import json

from architecture import DEFAULT_ARCH, ROOT
from experiment_port_interaction import family, fit, load


def main():
    ports=json.loads((DEFAULT_ARCH/'SRB_Port.json').read_text())['Port']
    families=sorted({family(x['Name']) for x in ports})
    lookup={name:i for i,name in enumerate(families)}
    port_ids=[lookup[family(x['Name'])] for x in ports]
    table=fit(load('development'),'pair_direction',20)
    count=len(families)
    values=[0.0]*(count*count*9)
    for (a,b,dx,dy),value in table.items():
        values[((lookup[a]*count+lookup[b])*3+dx+1)*3+dy+1]=value
    body='\n'.join([
        '// Generated from development labels and spatial-model predictions.',
        '#pragma once','#include <array>','namespace port_model {',
        f'constexpr int FAMILIES={count};',
        f'constexpr std::array<int,{len(port_ids)}> family={{{",".join(map(str,port_ids))}}};',
        f'constexpr std::array<double,{len(values)}> residual={{{",".join(format(x,".17g") for x in values)}}};',
        '} // namespace port_model',''])
    out=ROOT/'src/port_model.hpp';out.write_text(body)
    print(json.dumps({'path':str(out),'bytes':out.stat().st_size,
                      'families':count,'nonzero_entries':len(table)}))


if __name__=='__main__':main()
