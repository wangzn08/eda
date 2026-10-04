"""Measure low-cardinality spatial residual tables on fixed dev/validation splits."""
import collections
import csv
import json
import math
import re
import time

from architecture import ROOT
from experiment_displacement import DATA, weighted_score

PIN = re.compile(r'^SRB_(\d+)_(\d+)/')


def load(split, stem='approximate'):
    rows=[]
    with (DATA/f'{split}.golden.csv').open(newline='') as f, (DATA/f'{split}.{stem}.csv').open(newline='') as g:
        for truth, base in zip(csv.DictReader(f),csv.DictReader(g)):
            if truth['From']!=base['From'] or truth['To']!=base['To']:
                raise ValueError('Different row order')
            sx,sy=map(int,PIN.match(truth['From']).groups())
            tx,ty=map(int,PIN.match(truth['To']).groups())
            rows.append((sx,sy,tx,ty,int(truth['delay']),int(base['delay'])))
    return rows


def feature(row,family):
    sx,sy,tx,ty,_,_=row
    if family=='x_pair': return (sx//10,tx//10,(ty>sy)-(ty<sy))
    if family=='y_pair': return (sy//50,ty//50,(tx>sx)-(tx<sx))
    if family=='source_cell': return (sx//10,sy//50)
    if family=='target_cell': return (tx//10,ty//50)
    if family=='x_pair_source_y': return (sx//10,tx//10,(ty>sy)-(ty<sy),sy//50)
    if family=='x_pair_target_y': return (sx//10,tx//10,(ty>sy)-(ty<sy),ty//50)
    if family=='y_pair_source_x': return (sy//50,ty//50,(tx>sx)-(tx<sx),sx//10)
    if family=='y_pair_target_x': return (sy//50,ty//50,(tx>sx)-(tx<sx),tx//10)
    raise ValueError(family)


def fit(rows,families,prior):
    features=[[feature(row,family) for row in rows] for family in families]
    tables=[{} for _ in families]
    for _ in range(4):
        for i,keys in enumerate(features):
            sums=collections.defaultdict(lambda:[0.,0])
            for index,row in enumerate(rows):
                residual=row[4]-row[5]
                for j in range(len(families)):
                    if i!=j: residual-=tables[j].get(features[j][index],0)
                record=sums[keys[index]]
                record[0]+=residual;record[1]+=1
            tables[i]={key:total/(count+prior) for key,(total,count) in sums.items()}
    return tables


def evaluate(rows,families,tables):
    scores=[]
    groups=collections.defaultdict(list)
    for row in rows:
        sx,sy,tx,ty,golden,base=row
        if golden==0: continue
        estimate=max(0,round(base+sum(table.get(feature(row,family),0)
                                      for family,table in zip(families,tables))))
        score=weighted_score(golden,estimate)
        scores.append(score)
        distance=abs(tx-sx)+abs(ty-sy)
        groups['short' if distance<=20 else 'middle' if distance<=200 else 'far'].append(score)
    return {'score':sum(scores)/len(scores),
            'groups':{key:{'rows':len(value),'score':sum(value)/len(value)}
                      for key,value in groups.items()}}


def main():
    started=time.monotonic()
    dev=load('development'); val=load('validation')
    designs=[('x_pair',),('y_pair',),('source_cell','target_cell'),
             ('x_pair','y_pair'),('x_pair','y_pair','source_cell','target_cell')]
    candidates=[]
    for families in designs:
        tables=fit(dev,families,100)
        candidates.append({'features':families,'table_entries':[len(x) for x in tables],
                           'metrics':evaluate(val,families,tables)})
    report={'baseline':evaluate(val,(),()),'candidates':candidates,
            'development_rows':len(dev),'validation_rows':len(val),
            'elapsed_seconds':time.monotonic()-started,'holdout_used':False}
    (ROOT/'reports/P4-spatial-residual.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
