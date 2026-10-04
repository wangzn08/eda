"""Residual detail beyond port family and direction, fitted on development only."""
import collections
import csv
import json
import re
import time

from architecture import ROOT
from experiment_displacement import DATA, weighted_score
from experiment_port_interaction import family

PIN=re.compile(r'^SRB_(\d+)_(\d+)/(.+)$')


def load(split):
    rows=[]
    with (DATA/f'{split}.golden.csv').open(newline='') as f, (DATA/f'{split}.port.csv').open(newline='') as g:
        for a,b in zip(csv.DictReader(f),csv.DictReader(g)):
            if (a['From'],a['To'])!=(b['From'],b['To']):raise ValueError('row mismatch')
            sx,sy,sp=PIN.fullmatch(a['From']).groups()
            tx,ty,tp=PIN.fullmatch(a['To']).groups()
            rows.append((sp,tp,int(tx)-int(sx),int(ty)-int(sy),int(a['delay']),int(b['delay'])))
    return rows


def key(row,kind):
    sp,tp,dx,dy,_,_=row
    direction=((dx>0)-(dx<0),(dy>0)-(dy<0))
    if kind=='source_port_direction':return (sp,*direction)
    if kind=='target_port_direction':return (tp,*direction)
    if kind=='family_pair_direction_distance':return (family(sp),family(tp),*direction,min(7,(abs(dx)+abs(dy))//70))
    if kind=='family_pair_direction_dx':return (family(sp),family(tp),*direction,min(5,abs(dx)//20))
    if kind=='family_pair_direction_dy':return (family(sp),family(tp),*direction,min(7,abs(dy)//70))
    raise ValueError(kind)


def fit(rows,kind,prior):
    sums=collections.defaultdict(lambda:[0.,0])
    for row in rows:
        s=sums[key(row,kind)];s[0]+=row[4]-row[5];s[1]+=1
    return {k:v/(n+prior) for k,(v,n) in sums.items()}


def evaluate(rows,kind,table):
    total=0.; groups=collections.defaultdict(lambda:[0,0.])
    for row in rows:
        if row[4]==0:continue
        value=max(0,round(row[5]+table.get(key(row,kind),0)))
        score=weighted_score(row[4],value);total+=score
        distance=abs(row[2])+abs(row[3])
        group='short' if distance<=20 else 'middle' if distance<=200 else 'far'
        entry=groups[group];entry[0]+=1;entry[1]+=score
    return {'score':total/len(rows),'groups':{k:{'rows':v[0],'score':v[1]/v[0]}
                                             for k,v in groups.items()}}


def main():
    start=time.monotonic();dev=load('development');val=load('validation')
    results=[]
    for kind in ('source_port_direction','target_port_direction',
                 'family_pair_direction_distance','family_pair_direction_dx',
                 'family_pair_direction_dy'):
        for prior in (20,100):
            table=fit(dev,kind,prior)
            results.append({'kind':kind,'prior':prior,'entries':len(table),
                            'metrics':evaluate(val,kind,table)})
    report={'baseline':evaluate(val,'source_port_direction',{}),
            'candidates':results,'elapsed_seconds':time.monotonic()-start,
            'holdout_used':False}
    (ROOT/'reports/P4-port-refinement.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'baseline':report['baseline']['score'],
                      'candidates':[{'kind':x['kind'],'prior':x['prior'],
                                     'entries':x['entries'],'score':x['metrics']['score']}
                                    for x in results]},indent=2))


if __name__=='__main__':main()
