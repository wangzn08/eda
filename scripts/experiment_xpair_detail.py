"""Probe whether source/target column interaction helps after both column terms."""
import collections
import json
import time

from architecture import ROOT
from experiment_displacement import weighted_score
from experiment_region_port import load


def key(row,kind):
    sx,sy,tx,ty,_,_,_,_=row
    dy=(ty>sy)-(ty<sy)
    if kind=='exact_pair':return sx,tx
    if kind=='exact_pair_y_sign':return sx,tx,dy
    if kind=='half_pair_y_sign':return sx//2,tx//2,dy
    if kind=='fifth_pair_y_sign':return sx//5,tx//5,dy
    if kind=='exact_signed_displacement':return tx-sx,dy
    raise ValueError(kind)


def fit(rows,kind,prior):
    sums=collections.defaultdict(lambda:[0.,0])
    for row in rows:
        entry=sums[key(row,kind)];entry[0]+=row[6]-row[7];entry[1]+=1
    return {k:value/(count+prior) for k,(value,count) in sums.items()}


def score(rows,kind,table):
    total=0.;count=0
    for row in rows:
        if row[6]==0:continue
        pred=max(0,round(row[7]+table.get(key(row,kind),0)))
        total+=weighted_score(row[6],pred);count+=1
    return total/count


def main():
    start=time.monotonic()
    dev=load('development','target-x');val=load('validation','target-x')
    results=[]
    for kind in ('exact_pair','exact_pair_y_sign','half_pair_y_sign',
                 'fifth_pair_y_sign','exact_signed_displacement'):
        for prior in (20,100):
            table=fit(dev,kind,prior)
            results.append({'kind':kind,'prior':prior,'entries':len(table),
                            'validation_score':score(val,kind,table)})
    report={'baseline':score(val,'exact_pair',{}),'candidates':results,
            'elapsed_seconds':time.monotonic()-start,'holdout_used':False}
    (ROOT/'reports/V2-xpair-detail.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
