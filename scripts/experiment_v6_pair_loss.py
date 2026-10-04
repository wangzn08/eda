"""Optimize the compact endpoint-pair correction for the official score."""
import collections
import json
import math
import statistics
import time

from architecture import ROOT
from experiment_region_port import load
from experiment_v6_port_pair import score


def key(row):return row[4],row[5]


def fit_weighted(rows,alpha,prior,cap):
    sums=collections.defaultdict(lambda:[0.,0.])
    for row in rows:
        y=row[6]
        if y<=0:continue
        w=min(cap,(500/max(y,20))**alpha)
        entry=sums[key(row)]
        entry[0]+=w*(y-row[7]);entry[1]+=w
    return {k:s/(w+prior) for k,(s,w) in sums.items()}


def fit_median(rows,prior):
    groups=collections.defaultdict(list)
    for row in rows:
        if row[6]>0:groups[key(row)].append(row[6]-row[7])
    return {k:statistics.median(values)*len(values)/(len(values)+prior)
            for k,values in groups.items()}


def main():
    start=time.monotonic()
    dev,val=load('development','v5-geometry-fused'),load('validation','v5-geometry-fused')
    results=[]
    for alpha in (0,0.5,1,1.5,2):
        for cap in (3,10):
            for prior in (0,1,2,5):
                table=fit_weighted(dev,alpha,prior,cap)
                item={'loss':'weighted_mean','alpha':alpha,'cap':cap,'prior':prior,
                      'entries':len(table),'validation_score':score(val,'pair',table)}
                results.append(item)
                print(item,flush=True)
    for prior in (0,1,2,5):
        table=fit_median(dev,prior)
        item={'loss':'median','prior':prior,'entries':len(table),
              'validation_score':score(val,'pair',table)}
        results.append(item);print(item,flush=True)
    report={'baseline':score(val,'pair',{}),'best':max(results,key=lambda x:x['validation_score']),
            'candidates':results,'elapsed_seconds':time.monotonic()-start,'holdout_used':False}
    (ROOT/'reports/V6-pair-loss-research.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
