"""Export development-only V3 route and momentum residuals to C++ tables."""
import json

from architecture import Architecture, ROOT
from experiment_region_port import load
from experiment_route_confidence import fit as route_fit
from experiment_route_combined import apply, score
from experiment_route_momentum import fit as momentum_fit


def initial_code(value):
    return {'A': 0, 'S': 1, 'Z': 2}.get(value, 3)


def main():
    arch=Architecture()
    outgoing={n['from']:(n['delta x'],n['delta y']) for n in arch.nets}
    incoming={n['to']:(n['delta x'],n['delta y']) for n in arch.nets}
    dev,val=load('development','v2'),load('validation','v2')
    route=route_fit(dev,'route_ports',20)
    dev_after=apply(dev,'route',route,outgoing,incoming)
    val_after=apply(val,'route',route,outgoing,incoming)
    momentum=momentum_fit(dev_after,'source_port_momentum',20,outgoing,incoming)
    final=apply(val_after,'momentum',momentum,outgoing,incoming)
    route_values=[0.]*(3*10*4*4*4)
    for (kind,detour,source,target,bucket),value in route.items():
        idx=((((kind*10+detour)*4+initial_code(source))*4+initial_code(target))*4+bucket)
        route_values[idx]=value
    momentum_values=[0.]*((len(arch.ports)+1)*4*4*3*3)
    port_ids=arch.port_ids
    for (port,direction,bucket,xsign,ysign),value in momentum.items():
        port_id=len(arch.ports) if port=='other' else port_ids[port]
        idx=((((port_id*4+direction)*4+bucket)*3+xsign+1)*3+ysign+1)
        momentum_values[idx]=value
    output=ROOT/'src/route_v3_model.hpp'
    output.write_text('\n'.join([
        '// Generated from development labels and frozen V2 predictions only.',
        '#pragma once','#include <array>','namespace route_v3_model {',
        f'constexpr std::array<double,{len(route_values)}> route={{{",".join(format(x,".17g") for x in route_values)}}};',
        f'constexpr std::array<double,{len(momentum_values)}> momentum={{{",".join(format(x,".17g") for x in momentum_values)}}};',
        '} // namespace route_v3_model','']))
    result={'output':str(output),'bytes':output.stat().st_size,
            'route_nonzero':len(route),'route_dense':len(route_values),
            'momentum_nonzero':len(momentum),'momentum_dense':len(momentum_values),
            'python_validation_score':score(final),'holdout_used':False}
    (ROOT/'reports/V3-export.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
