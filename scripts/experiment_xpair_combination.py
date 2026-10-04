"""Compare small signed-displacement and exact-column-pair residual stages."""
import collections
import json
import time

from architecture import ROOT
from experiment_displacement import weighted_score
from experiment_region_port import load
from experiment_xpair_detail import key


def fit_stage(rows,predictions,kind,prior):
    sums=collections.defaultdict(lambda:[0.,0])
    for row,pred in zip(rows,predictions):
        entry=sums[key(row,kind)]
        entry[0]+=row[6]-pred;entry[1]+=1
    return {k:value/(count+prior) for k,(value,count) in sums.items()}


def apply_stage(rows,predictions,kind,table):
    return [max(0,round(pred+table.get(key(row,kind),0)))
            for row,pred in zip(rows,predictions)]


def score(rows,predictions):
    values=[weighted_score(row[6],pred) for row,pred in zip(rows,predictions) if row[6]>0]
    return sum(values)/len(values)


def main():
    started=time.monotonic()
    dev=load('development','target-x');val=load('validation','target-x')
    designs=[('exact_signed_displacement',),('exact_pair',),
             ('exact_signed_displacement','exact_pair'),
             ('exact_pair','exact_signed_displacement')]
    results=[]
    for kinds in designs:
        train_pred=[row[7] for row in dev]
        val_pred=[row[7] for row in val]
        entries=[]
        for kind in kinds:
            table=fit_stage(dev,train_pred,kind,20)
            entries.append(len(table))
            train_pred=apply_stage(dev,train_pred,kind,table)
            val_pred=apply_stage(val,val_pred,kind,table)
        results.append({'stages':kinds,'entries':entries,
                        'validation_score':score(val,val_pred)})
    report={'baseline':score(val,[row[7] for row in val]),
            'candidates':results,'elapsed_seconds':time.monotonic()-started,
            'holdout_used':False}
    (ROOT/'reports/V2-xpair-combination.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
