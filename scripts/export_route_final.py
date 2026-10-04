"""Export route -> forced detour -> source momentum, fit on development only."""
import json

from architecture import Architecture,ROOT
from experiment_region_port import load
from experiment_route_confidence import fit as route_fit
from experiment_route_momentum import fit as momentum_fit
from experiment_forced_route import fit as forced_fit,key as forced_key
from experiment_route_combined import apply,score
from export_route_v3 import initial_code


def main():
    arch=Architecture()
    outgoing={n['from']:(n['delta x'],n['delta y']) for n in arch.nets}
    incoming={n['to']:(n['delta x'],n['delta y']) for n in arch.nets}
    dev,val=load('development','v2'),load('validation','v2')
    route=route_fit(dev,'route_ports',20)
    dev=apply(dev,'route',route,outgoing,incoming)
    val=apply(val,'route',route,outgoing,incoming)
    forced=forced_fit(dev,'detour_exact',20,outgoing,incoming)
    def apply_forced(rows):
        return [(*row[:7],max(0,round(row[7]+forced.get(forced_key(row,'detour_exact',outgoing,incoming),0))))
                for row in rows]
    dev=apply_forced(dev)
    val=apply_forced(val)
    momentum=momentum_fit(dev,'source_port_momentum',20,outgoing,incoming)
    val=apply(val,'momentum',momentum,outgoing,incoming)
    route_values=[0.]*(3*10*4*4*4)
    for (kind,detour,source,target,bucket),value in route.items():
        idx=((((kind*10+detour)*4+initial_code(source))*4+initial_code(target))*4+bucket)
        route_values[idx]=value
    forced_values=[0.]*(51*4*2*2)
    for (detour,bucket,source,target),value in forced.items():
        forced_values[(((detour*4+bucket)*2+int(source))*2+int(target))]=value
    momentum_values=[0.]*((len(arch.ports)+1)*4*4*3*3)
    for (port,direction,bucket,xsign,ysign),value in momentum.items():
        port_id=len(arch.ports) if port=='other' else arch.port_ids[port]
        momentum_values[((((port_id*4+direction)*4+bucket)*3+xsign+1)*3+ysign+1)]=value
    output=ROOT/'src/route_v3_final_model.hpp'
    output.write_text('\n'.join([
        '// Generated from development labels and frozen V2 predictions only.',
        '#pragma once','#include <array>','namespace route_v3_final_model {',
        f'constexpr std::array<double,{len(route_values)}> route={{{",".join(format(x,".17g") for x in route_values)}}};',
        f'constexpr std::array<double,{len(forced_values)}> forced={{{",".join(format(x,".17g") for x in forced_values)}}};',
        f'constexpr std::array<double,{len(momentum_values)}> momentum={{{",".join(format(x,".17g") for x in momentum_values)}}};',
        '} // namespace route_v3_final_model','']))
    report={'path':str(output),'bytes':output.stat().st_size,
            'route_entries':len(route),'forced_entries':len(forced),'momentum_entries':len(momentum),
            'python_validation_score':score(val),'holdout_used':False}
    (ROOT/'reports/V3-final-export.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
