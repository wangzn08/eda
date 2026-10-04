"""Test geometry lower bounds implied by fixed first and last Net moves."""
import collections
import json
import time

from architecture import Architecture, ROOT
from experiment_displacement import weighted_score
from experiment_region_port import load


def features(row, outgoing, incoming):
    sx, sy, tx, ty, sp, tp, _, _ = row
    dx, dy=tx-sx,ty-sy
    first=outgoing.get(sp,(0,0))
    last=incoming.get(tp,(0,0))
    direct=abs(dx)+abs(dy)
    forced=(abs(first[0])+abs(first[1])+abs(last[0])+abs(last[1])
            +abs(dx-first[0]-last[0])+abs(dy-first[1]-last[1]))
    detour=max(0,forced-direct)
    distance=0 if direct<16 else 1 if direct<64 else 2 if direct<256 else 3
    return detour,distance,bool(sp in outgoing),bool(tp in incoming),dx,dy


def key(row,kind,outgoing,incoming):
    detour,distance,source,target,dx,dy=features(row,outgoing,incoming)
    xsign,ysign=(dx>0)-(dx<0),(dy>0)-(dy<0)
    if kind=='detour_exact':return min(50,detour),distance,source,target
    if kind=='detour_direction':return min(50,detour),distance,xsign,ysign
    if kind=='detour_coarse':return min(10,detour//4),distance,source,target,xsign,ysign
    if kind=='detour_port':return min(20,detour//2),distance,row[4][0],row[5][0]
    raise ValueError(kind)


def fit(rows,kind,prior,outgoing,incoming):
    sums=collections.defaultdict(lambda:[0.,0])
    for row in rows:
        if row[6]<=0:continue
        entry=sums[key(row,kind,outgoing,incoming)]
        entry[0]+=row[6]-row[7]
        entry[1]+=1
    return {k:total/(count+prior) for k,(total,count) in sums.items()}


def evaluate(rows,kind,table,outgoing,incoming):
    total=0.;count=0
    for row in rows:
        if row[6]<=0:continue
        pred=max(0,round(row[7]+table.get(key(row,kind,outgoing,incoming),0)))
        total+=weighted_score(row[6],pred);count+=1
    return total/count


def main():
    start=time.monotonic()
    arch=Architecture()
    outgoing={n['from']:(n['delta x'],n['delta y']) for n in arch.nets}
    incoming={n['to']:(n['delta x'],n['delta y']) for n in arch.nets}
    dev,val=load('development','v3'),load('validation','v3')
    baseline=evaluate(val,'detour_exact',{},outgoing,incoming)
    candidates=[]
    for kind in ('detour_exact','detour_direction','detour_coarse','detour_port'):
        for prior in (20,100):
            table=fit(dev,kind,prior,outgoing,incoming)
            candidates.append({'kind':kind,'prior':prior,'entries':len(table),
                               'validation_score':evaluate(val,kind,table,outgoing,incoming)})
    report={'baseline':baseline,'candidates':candidates,'elapsed_seconds':time.monotonic()-start,
            'holdout_used':False,
            'note':'Forced route length is a Manhattan lower bound based on fixed endpoint Net vectors, not an exact path length.'}
    (ROOT/'reports/V3-forced-route.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
