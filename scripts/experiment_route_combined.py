"""Check whether Block-route and Net-direction corrections add independently."""
import json
import time

from architecture import Architecture, ROOT
from experiment_displacement import weighted_score
from experiment_region_port import load
from experiment_route_confidence import fit as route_fit, key as route_key
from experiment_route_momentum import fit as momentum_fit, key as momentum_key


def apply(rows, kind, table, outgoing, incoming):
    transformed=[]
    for row in rows:
        if kind=='route': delta=table.get(route_key(row,'route_ports'),0)
        else: delta=table.get(momentum_key(row,'source_port_momentum',outgoing,incoming),0)
        transformed.append((*row[:7],max(0,round(row[7]+delta))))
    return transformed


def score(rows):
    values=[weighted_score(row[6],row[7]) for row in rows if row[6]>0]
    return sum(values)/len(values)


def main():
    start=time.monotonic()
    arch=Architecture()
    outgoing={n['from']:(n['delta x'],n['delta y']) for n in arch.nets}
    incoming={n['to']:(n['delta x'],n['delta y']) for n in arch.nets}
    dev,val=load('development','v2'),load('validation','v2')
    outcomes=[]
    for order in (('route','momentum'),('momentum','route')):
        trained_dev,scored_val=dev,val
        stages=[]
        for kind in order:
            if kind=='route': table=route_fit(trained_dev,'route_ports',20)
            else: table=momentum_fit(trained_dev,'source_port_momentum',20,outgoing,incoming)
            trained_dev=apply(trained_dev,kind,table,outgoing,incoming)
            scored_val=apply(scored_val,kind,table,outgoing,incoming)
            stages.append({'kind':kind,'entries':len(table),'validation_score':score(scored_val)})
        outcomes.append({'order':order,'stages':stages})
    result={'baseline':score(val),'outcomes':outcomes,'holdout_used':False,
            'elapsed_seconds':time.monotonic()-start}
    (ROOT/'reports/V3-route-combined.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
