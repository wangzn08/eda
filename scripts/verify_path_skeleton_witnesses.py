"""Replay development traces through official arc/net geometry, no holdout."""
import csv,json,collections
from architecture import ROOT,Architecture
arch=Architecture();names=[p['Name'] for p in arch.ports]
net_to={n['to']:n for n in arch.nets};groups=collections.defaultdict(list)
with (ROOT/'out/evaluation/v62-skeleton.states.csv').open() as f:
    for r in csv.DictReader(f):groups[int(r['row'])].append({k:int(v) for k,v in r.items()})
with (ROOT/'out/evaluation/v62-skeleton.request.csv').open() as f:requests=list(csv.DictReader(f))
def transition(a,b):
    x,y,port=a;tx,ty,tp=b;possible=[]
    if (x,y)==(tx,ty) and port==tp:possible.append(0)
    if (x,y)==(tx,ty) and (port,tp) in arch.arc_delays:possible.append(arch.arc_delays[port,tp])
    net=net_to.get(tp)
    if net:
        cost=0 if port==net['from'] else arch.arc_delays.get((port,net['from']))
        if cost is not None:
            move=arch.move(x,y,net['delta x'],net['delta y'])
            if move and move[0]==(tx,ty):possible.append(cost+move[1]+net.get('delay',0))
    if not possible:raise ValueError(f'No witness {a} -> {b}')
    return min(possible)
patterns=collections.Counter();verified=0
for row,states in sorted(groups.items()):
    req=requests[row-1];a,sp,_=arch.pin(req['From']);b,tp,_=arch.pin(req['To'])
    nodes=[(*a,sp)]+[(s['x'],s['y'],names[s['port']]) for s in states]+[(*b,tp)]
    cost=sum(transition(a,b) for a,b in zip(nodes,nodes[1:]))
    assert cost==states[0]['delay'],(row,cost,states[0]['delay']);verified+=1
    for a,b in zip(nodes[1:-1],nodes[2:-1]):
        if a[2]==b[2]:patterns[(a[2],b[0]-a[0],b[1]-a[1])]+=1
items=[]
# Geometry-only translation sample spans the physical grid, including walls/boundaries.
sites=sorted(arch.sites)[::max(1,len(arch.sites)//1000)]
for (port,dx,dy),count in patterns.most_common(12):
    net=net_to[port];arc=arch.arc_delays[(port,net['from'])];valid=0;changed=0;costs=collections.Counter()
    for x,y in sites:
        m=arch.move(x,y,net['delta x'],net['delta y'])
        if m:
            valid+=1;changed+=m[0]!=(x+dx,y+dy);costs[arc+net.get('delay',0)+m[1]]+=1
    items.append({'port':port,'observed_displacement':[dx,dy],'development_occurrences':count,
                  'arc_delay_ps':arc,'net_vector':[net['delta x'],net['delta y']],
                  'translation_sites':len(sites),'valid_translations':valid,
                  'changed_displacement_translations':changed,'translated_cost_histogram':dict(costs)})
report={'development_paths_replayed':verified,'exact_cost_matches':verified,'holdout_used':False,
        'closed_port_cycles':items,'scope':'Every sampled path replayed with actual arc/net moves; translation sample is geometric evidence, not exhaustive proof or query-time benchmark.'}
(ROOT/'reports/V63-skeleton-witnesses.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
