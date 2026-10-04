"""Test hierarchical endpoint-pair corrections under a bounded model budget."""
import collections
import json
import time

from architecture import ROOT
from experiment_region_port import load
from experiment_displacement import weighted_score
from experiment_port_interaction import family


def key(row,kind):
    sx,sy,tx,ty,sp,tp,_,_=row
    dx,dy=tx-sx,ty-sy
    xs,ys=(dx>0)-(dx<0),(dy>0)-(dy<0)
    if kind=='pair':return sp,tp
    if kind=='pair_xsign':return sp,tp,xs
    if kind=='pair_ysign':return sp,tp,ys
    if kind=='pair_signs':return sp,tp,xs,ys
    if kind=='pair_dy100':return sp,tp,min(5,abs(dy)//100),ys
    if kind=='pair_dx32':return sp,tp,min(3,abs(dx)//32),xs
    if kind=='pair_short':return sp,tp,int(abs(dx)<20),int(abs(dy)<40)
    if kind=='family_pair_dy20':return family(sp),family(tp),min(5,abs(dy)//20),ys
    if kind=='family_pair_dx16':return family(sp),family(tp),min(5,abs(dx)//16),xs
    if kind=='family_pair_short':return family(sp),family(tp),min(4,abs(dx)//10),min(4,abs(dy)//10)
    raise ValueError(kind)


def fit(rows,kind,prior):
    sums=collections.defaultdict(lambda:[0.,0])
    for row in rows:
        if row[6]<=0:continue
        entry=sums[key(row,kind)]
        entry[0]+=row[6]-row[7]
        entry[1]+=1
    return {k:total/(count+prior) for k,(total,count) in sums.items()}


def score(rows,kind,table):
    total=0.;count=0
    for row in rows:
        if row[6]<=0:continue
        pred=max(0,round(row[7]+table.get(key(row,kind),0)))
        total+=weighted_score(row[6],pred);count+=1
    return total/count


def main():
    start=time.monotonic()
    results=[]
    kinds=('pair','pair_xsign','pair_ysign','pair_signs','pair_dy100',
           'pair_dx32','pair_short','family_pair_dy20',
           'family_pair_dx16','family_pair_short')
    for stem in ('v4-horizontal','v5-geometry-fused'):
        dev,val=load('development',stem),load('validation',stem)
        baseline=score(val,'pair',{})
        for kind in kinds:
            for prior in (20,100,500):
                table=fit(dev,kind,prior)
                item={'stem':stem,'kind':kind,'prior':prior,'entries':len(table),
                      'validation_score':score(val,kind,table),'baseline':baseline}
                results.append(item)
                print(item,flush=True)
    report={'candidates':results,'elapsed_seconds':time.monotonic()-start,
            'holdout_used':False}
    (ROOT/'reports/V6-port-pair-research.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
