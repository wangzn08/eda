"""Explore regional port corrections after the frozen v1 model.

Only development labels fit parameters. Validation selects candidates.
The final holdout is intentionally untouched.
"""
import collections
import csv
import json
import re
import time

from architecture import ROOT
from experiment_displacement import DATA, weighted_score
from experiment_port_interaction import family

PIN=re.compile(r'^SRB_(\d+)_(\d+)/(.+)$')


def load(split,stem='port'):
    rows=[]
    with (DATA/f'{split}.golden.csv').open(newline='') as f, (DATA/f'{split}.{stem}.csv').open(newline='') as g:
        for truth,prediction in zip(csv.DictReader(f),csv.DictReader(g)):
            if (truth['From'],truth['To'])!=(prediction['From'],prediction['To']):
                raise ValueError('Endpoint order mismatch')
            sx,sy,sp=PIN.fullmatch(truth['From']).groups()
            tx,ty,tp=PIN.fullmatch(truth['To']).groups()
            rows.append((int(sx),int(sy),int(tx),int(ty),sp,tp,
                         int(truth['delay']),int(prediction['delay'])))
    return rows


def key(row,kind):
    sx,sy,tx,ty,sp,tp,_,_=row
    direction=((tx>sx)-(tx<sx),(ty>sy)-(ty<sy))
    if kind=='source_family_x_dir':return (family(sp),sx//10,*direction)
    if kind=='target_family_x_dir':return (family(tp),tx//10,*direction)
    if kind=='source_family_y_dir':return (family(sp),sy//50,*direction)
    if kind=='target_family_y_dir':return (family(tp),ty//50,*direction)
    if kind=='source_port_x':return (sp,sx//10)
    if kind=='target_port_x':return (tp,tx//10)
    if kind=='source_port_y':return (sp,sy//50)
    if kind=='target_port_y':return (tp,ty//50)
    raise ValueError(kind)


def fit(rows,kind,prior):
    sums=collections.defaultdict(lambda:[0.,0])
    for row in rows:
        entry=sums[key(row,kind)]
        entry[0]+=row[6]-row[7]
        entry[1]+=1
    return {k:total/(count+prior) for k,(total,count) in sums.items()}


def evaluate(rows,kind,table):
    scores=[]
    groups=collections.defaultdict(list)
    for row in rows:
        if row[6]==0:continue
        pred=max(0,round(row[7]+table.get(key(row,kind),0)))
        value=weighted_score(row[6],pred)
        scores.append(value)
        distance=abs(row[2]-row[0])+abs(row[3]-row[1])
        groups['short' if distance<=20 else 'middle' if distance<=200 else 'far'].append(value)
    return {'score':sum(scores)/len(scores),
            'groups':{k:{'rows':len(v),'score':sum(v)/len(v)} for k,v in groups.items()}}


def main():
    started=time.monotonic()
    development=load('development');validation=load('validation')
    kinds=('source_family_x_dir','target_family_x_dir',
           'source_family_y_dir','target_family_y_dir',
           'source_port_x','target_port_x','source_port_y','target_port_y')
    candidates=[]
    for kind in kinds:
        for prior in (20,100):
            table=fit(development,kind,prior)
            candidates.append({'kind':kind,'prior':prior,'entries':len(table),
                               'metrics':evaluate(validation,kind,table)})
    result={'baseline':evaluate(validation,kinds[0],{}),
            'development_rows':len(development),'validation_rows':len(validation),
            'candidates':candidates,'elapsed_seconds':time.monotonic()-started,
            'holdout_used':False}
    (ROOT/'reports/V2-region-port.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'baseline':result['baseline']['score'],
                      'candidates':[{'kind':r['kind'],'prior':r['prior'],
                                     'entries':r['entries'],'score':r['metrics']['score']}
                                    for r in candidates]},indent=2))


if __name__=='__main__':main()
