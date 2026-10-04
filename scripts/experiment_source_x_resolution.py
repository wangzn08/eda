"""Choose source-column resolution for routing-family directional residuals."""
import collections
import json
import time

from architecture import ROOT
from experiment_displacement import weighted_score
from experiment_port_interaction import family
from experiment_region_port import load


def key(row,width):
    sx,sy,tx,ty,sp,tp,_,_=row
    return family(sp),sx//width,(tx>sx)-(tx<sx),(ty>sy)-(ty<sy)


def fit(rows,width,prior):
    sums=collections.defaultdict(lambda:[0.,0])
    for row in rows:
        item=sums[key(row,width)];item[0]+=row[6]-row[7];item[1]+=1
    return {k:value/(count+prior) for k,(value,count) in sums.items()}


def score(rows,width,table):
    total=0.;count=0
    for row in rows:
        if row[6]==0:continue
        estimate=max(0,round(row[7]+table.get(key(row,width),0)))
        total+=weighted_score(row[6],estimate);count+=1
    return total/count


def main():
    start=time.monotonic()
    dev=load('development');val=load('validation')
    results=[]
    for width in (1,2,3,5,8,10,15,20):
        for prior in (20,100):
            table=fit(dev,width,prior)
            results.append({'width':width,'prior':prior,'entries':len(table),
                            'validation_score':score(val,width,table)})
    report={'baseline':score(val,10,{}),'candidates':results,
            'elapsed_seconds':time.monotonic()-start,'holdout_used':False}
    (ROOT/'reports/V2-source-x-resolution.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
