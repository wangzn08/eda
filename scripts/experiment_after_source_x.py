"""Explore remaining low-cost spatial residuals after source-column correction."""
import collections
import json
import time

from architecture import ROOT
from experiment_displacement import weighted_score
from experiment_port_interaction import family
from experiment_region_port import load


def key(row,kind):
    sx,sy,tx,ty,sp,tp,_,_=row
    direction=((tx>sx)-(tx<sx),(ty>sy)-(ty<sy))
    if kind=='target_x_family_dir':return family(tp),tx,*direction
    if kind=='source_y25_family_dir':return family(sp),sy//25,*direction
    if kind=='target_y25_family_dir':return family(tp),ty//25,*direction
    if kind=='source_y10_family_dir':return family(sp),sy//10,*direction
    if kind=='target_y10_family_dir':return family(tp),ty//10,*direction
    if kind=='source_port_x_dir':return sp,sx,*direction
    if kind=='target_port_x_dir':return tp,tx,*direction
    raise ValueError(kind)


def fit(rows,kind,prior):
    sums=collections.defaultdict(lambda:[0.,0])
    for row in rows:
        v=sums[key(row,kind)];v[0]+=row[6]-row[7];v[1]+=1
    return {k:total/(count+prior) for k,(total,count) in sums.items()}


def score(rows,kind,table):
    total=0.;count=0
    for row in rows:
        if row[6]==0:continue
        pred=max(0,round(row[7]+table.get(key(row,kind),0)))
        total+=weighted_score(row[6],pred);count+=1
    return total/count


def main():
    start=time.monotonic()
    dev=load('development','source-x');val=load('validation','source-x')
    kinds=('target_x_family_dir','source_y25_family_dir','target_y25_family_dir',
           'source_y10_family_dir','target_y10_family_dir',
           'source_port_x_dir','target_port_x_dir')
    results=[]
    for kind in kinds:
        for prior in (20,100):
            table=fit(dev,kind,prior)
            results.append({'kind':kind,'prior':prior,'entries':len(table),
                            'validation_score':score(val,kind,table)})
    result={'baseline':score(val,kinds[0],{}),'candidates':results,
            'elapsed_seconds':time.monotonic()-start,'holdout_used':False}
    (ROOT/'reports/V2-after-source-x.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
