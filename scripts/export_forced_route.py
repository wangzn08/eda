"""Export the development-fitted endpoint-forced detour correction."""
import json

from architecture import Architecture,ROOT
from experiment_region_port import load
from experiment_forced_route import fit,evaluate


def main():
    arch=Architecture()
    outgoing={n['from']:(n['delta x'],n['delta y']) for n in arch.nets}
    incoming={n['to']:(n['delta x'],n['delta y']) for n in arch.nets}
    table=fit(load('development','v3'),'detour_exact',20,outgoing,incoming)
    values=[0.]*(51*4*2*2)
    for (detour,bucket,source,target),value in table.items():
        idx=(((detour*4+bucket)*2+int(source))*2+int(target))
        values[idx]=value
    path=ROOT/'src/forced_route_model.hpp'
    path.write_text('\n'.join([
        '// Generated from development labels and frozen V3 predictions only.',
        '#pragma once','#include <array>','namespace forced_route_model {',
        f'constexpr std::array<double,{len(values)}> residual={{{",".join(format(x,".17g") for x in values)}}};',
        '} // namespace forced_route_model','']))
    result={'path':str(path),'bytes':path.stat().st_size,'nonzero_entries':len(table),
            'dense_entries':len(values),
            'python_validation_score':evaluate(load('validation','v3'),'detour_exact',table,outgoing,incoming),
            'holdout_used':False}
    (ROOT/'reports/V3-forced-export.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
