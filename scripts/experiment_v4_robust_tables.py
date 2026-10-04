"""Compare mean, median, and relative-error-weighted median V4 residuals."""
import collections
import json
import time

from architecture import ROOT
from experiment_region_port import load
from experiment_v4_interactions import key,score


def fit(rows,kind,method,prior=20):
    groups=collections.defaultdict(list)
    for row in rows:
        truth,base=row[6:]
        if truth<=0:continue
        groups[key(row,kind)].append((truth-base,1/truth))
    table={}
    for name,items in groups.items():
        if method=='mean':
            value=sum(x for x,_ in items)/len(items)
        else:
            items.sort(key=lambda x:x[0])
            if method=='median':
                value=items[(len(items)-1)//2][0]
            else:
                half=sum(weight for _,weight in items)/2
                total=0.;value=items[-1][0]
                for residual,weight in items:
                    total+=weight
                    if total>=half:
                        value=residual;break
        table[name]=value*len(items)/(len(items)+prior)
    return table


def apply(rows,kind,table):
    return [(*row[:7],max(0,round(row[7]+table.get(key(row,kind),0)))) for row in rows]


def main():
    start=time.monotonic()
    dev,val=load('development','v3-final'),load('validation','v3-final')
    order=('signed_dy_exact','target_port_dy16','source_port_dy16')
    outcomes=[]
    for method in ('mean','median','relative_median'):
        training,validation=dev,val
        stages=[]
        for kind in order:
            table=fit(training,kind,method)
            training=apply(training,kind,table)
            validation=apply(validation,kind,table)
            stages.append({'kind':kind,'entries':len(table),
                           'validation_score':score(validation,kind,{})})
        result={'method':method,'stages':stages}
        outcomes.append(result)
        print(result,flush=True)
    report={'baseline':score(val,order[0],{}),'outcomes':outcomes,
            'elapsed_seconds':time.monotonic()-start,'holdout_used':False}
    (ROOT/'reports/V4-robust-tables.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
