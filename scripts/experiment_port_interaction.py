"""Assess routing-port pair interactions after the spatial model."""
import collections
import csv
import json
import math
import re
import time

from architecture import ROOT
from experiment_displacement import DATA, weighted_score

PIN=re.compile(r'^SRB_(\d+)_(\d+)/(.+)$')


def family(port):
    return port.split('[',1)[0] if port.startswith('Z') else port[0]


def load(split):
    rows=[]
    with (DATA/f'{split}.golden.csv').open(newline='') as f, (DATA/f'{split}.spatial.csv').open(newline='') as g:
        for a,b in zip(csv.DictReader(f),csv.DictReader(g)):
            if (a['From'],a['To'])!=(b['From'],b['To']): raise ValueError('Row mismatch')
            sx,sy,sp=PIN.fullmatch(a['From']).groups()
            tx,ty,tp=PIN.fullmatch(a['To']).groups()
            dx,dy=int(tx)-int(sx),int(ty)-int(sy)
            rows.append((family(sp),family(tp),dx,dy,int(a['delay']),int(b['delay'])))
    return rows


def key(row,kind):
    sp,tp,dx,dy,_,_=row
    if kind=='pair':return sp,tp
    if kind=='pair_direction':return sp,tp,(dx>0)-(dx<0),(dy>0)-(dy<0)
    if kind=='pair_distance':return sp,tp,min(7,(abs(dx)+abs(dy))//64)
    if kind=='pair_dx':return sp,tp,min(7,abs(dx)//16)
    if kind=='pair_dy':return sp,tp,min(7,abs(dy)//70)
    raise ValueError(kind)


def fit(rows,kind,prior):
    sums=collections.defaultdict(lambda:[0.,0])
    for row in rows:
        r=sums[key(row,kind)];r[0]+=row[4]-row[5];r[1]+=1
    return {k:s/(n+prior) for k,(s,n) in sums.items()}


def evaluate(rows,kind,table):
    score=0.;groups=collections.defaultdict(lambda:[0,0.])
    for row in rows:
        gold=row[4]
        if gold==0:continue
        pred=max(0,round(row[5]+table.get(key(row,kind),0)))
        value=weighted_score(gold,pred);score+=value
        g=groups[row[0]+'->'+row[1]];g[0]+=1;g[1]+=value
    return {'score':score/len(rows),'main_groups':sorted(
        ({'pair':k,'rows':n,'score':v/n} for k,(n,v) in groups.items()),
        key=lambda x:x['rows'],reverse=True)[:10]}


def main():
    started=time.monotonic()
    dev=load('development');val=load('validation')
    candidates=[]
    for kind in ('pair','pair_direction','pair_distance','pair_dx','pair_dy'):
        for prior in (20,100):
            table=fit(dev,kind,prior)
            candidates.append({'kind':kind,'prior':prior,'entries':len(table),
                               'metrics':evaluate(val,kind,table)})
    result={'baseline':evaluate(val,'pair',{}),'candidates':candidates,
            'elapsed_seconds':time.monotonic()-started,'holdout_used':False}
    (ROOT/'reports/P4-port-interaction.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'baseline':result['baseline']['score'],
                      'candidates':[{'kind':x['kind'],'prior':x['prior'],
                                     'entries':x['entries'],'score':x['metrics']['score']}
                                    for x in candidates]},indent=2))


if __name__=='__main__':main()
