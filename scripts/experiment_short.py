"""P4 short-range model comparison; final holdout remains untouched."""
import csv
import json
import math
import time

from architecture import ROOT
from experiment_displacement import DATA, parse, predict, quantile, train, weighted_score


def load(name):
    with (DATA / f'{name}.golden.csv').open(newline='') as f:
        return [parse(row) for row in csv.DictReader(f)]


def summarize(rows, model, wx, wy):
    scores, errors = [], []
    for row in rows:
        if row[4] == 0:
            continue
        value = predict(row, model, wx, wy)
        scores.append(weighted_score(row[4], value))
        errors.append(abs(value-row[4])/row[4])
    errors.sort()
    return {'rows':len(rows),'score':sum(scores)/len(scores),
            'relative_error_p50':quantile(errors,.5),
            'relative_error_p95':quantile(errors,.95)}


def main():
    start=time.monotonic()
    dev=load('development')
    val=load('validation')
    near=lambda row: abs(row[0])+abs(row[1])<=20
    dev_near=[r for r in dev if near(r)]
    val_near=[r for r in val if near(r)]
    base=train(dev,8,16)
    baseline=summarize(val_near,base,8,16)
    candidates=[]
    for wx,wy in ((1,1),(2,2),(2,4),(4,4)):
        model=train(dev_near,wx,wy)
        candidates.append({'width_x':wx,'width_y':wy,'table_entries':len(model[-1]),
                           'short_validation':summarize(val_near,model,wx,wy)})
    report={'method':'Short-distance-only regularized displacement table',
            'development_near_rows':len(dev_near),'validation_near_rows':len(val_near),
            'distance_threshold':20,'baseline':baseline,'candidates':candidates,
            'elapsed_seconds':time.monotonic()-start,'holdout_used':False}
    (ROOT/'reports/P4-short.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
