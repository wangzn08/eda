"""Compare weighted displacement fitting against the official relative score."""
import csv
import json
import time

from architecture import ROOT
from experiment_displacement import DATA, parse, predict, quantile, train, weighted_score


def load(name):
    with (DATA / f'{name}.golden.csv').open(newline='') as f:
        return [parse(row) for row in csv.DictReader(f)]


def score(rows, model):
    values=[]
    groups={name:[] for name in ('short','middle','far')}
    for row in rows:
        if row[4]==0: continue
        pred=predict(row,model,8,16)
        s=weighted_score(row[4],pred)
        values.append(s)
        distance=abs(row[0])+abs(row[1])
        groups['short' if distance<=20 else 'middle' if distance<=200 else 'far'].append(s)
    return {'overall':sum(values)/len(values),
            'groups':{k:{'rows':len(v),'score':sum(v)/len(v)} for k,v in groups.items()}}


def main():
    start=time.monotonic()
    dev=load('development');val=load('validation')
    variants=[]
    for power in (0, .5, 1, 1.5, 2):
        model=train(dev,8,16,weight_power=power)
        variants.append({'weight_power':power,'metrics':score(val,model)})
    report={'method':'weighted squared-error fitting for displacement lookup',
            'weight':'(1000/max(100,golden))**power; development labels only',
            'variants':variants,'elapsed_seconds':time.monotonic()-start,
            'holdout_used':False}
    (ROOT/'reports/P4-relative-objective.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
