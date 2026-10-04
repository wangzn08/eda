"""Compress tree-discovered feature interactions into constant-time residual tables."""
import argparse
import collections
import json
import time

from architecture import ROOT
from experiment_displacement import weighted_score
from experiment_region_port import load
from experiment_port_interaction import family


def key(row,kind):
    sx,sy,tx,ty,sp,tp,_,_=row
    dx,dy=tx-sx,ty-sy
    if kind=='source_port_dy16':return sp,abs(dy)//16,(dy>0)-(dy<0)
    if kind=='target_port_dy16':return tp,abs(dy)//16,(dy>0)-(dy<0)
    if kind=='source_port_dx8':return sp,abs(dx)//8,(dx>0)-(dx<0)
    if kind=='target_port_dx8':return tp,abs(dx)//8,(dx>0)-(dx<0)
    if kind=='source_x_dy50':return sx,abs(dy)//50,(dy>0)-(dy<0)
    if kind=='target_x_dy50':return tx,abs(dy)//50,(dy>0)-(dy<0)
    if kind=='source_yphase_dy50':return sy%100,abs(dy)//50,(dy>0)-(dy<0)
    if kind=='target_yphase_dy50':return ty%100,abs(dy)//50,(dy>0)-(dy<0)
    if kind=='source_port_target_x10':return sp,tx//10
    if kind=='target_port_source_x10':return tp,sx//10
    if kind=='source_family_yphase':return family(sp),sy%100
    if kind=='target_family_yphase':return family(tp),ty%100
    if kind=='signed_dy_exact':return dy,(dx>0)-(dx<0)
    if kind=='target_port_dy8':return tp,abs(dy)//8,(dy>0)-(dy<0)
    if kind=='source_port_dy8':return sp,abs(dy)//8,(dy>0)-(dy<0)
    if kind=='target_port_yphase20':return tp,ty%100//20
    if kind=='source_port_yphase20':return sp,sy%100//20
    if kind=='target_port_x':return tp,tx
    if kind=='source_port_x':return sp,sx
    if kind=='target_port_gap_y':return tp,min(5,abs(dy)//100),ty//100
    if kind=='source_port_gap_y':return sp,min(5,abs(dy)//100),sy//100
    if kind=='signed_dx_dybucket':return dx,abs(dy)//32,(dy>0)-(dy<0)
    if kind=='dy_phase_exact':return dy,sy%100//10,ty%100//10
    if kind=='port_pair_distance':return family(sp),family(tp),abs(dy)//32,(dx>0)-(dx<0)
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
    parser=argparse.ArgumentParser()
    parser.add_argument('--stem',default='v3-final')
    args=parser.parse_args()
    start=time.monotonic()
    dev,val=load('development',args.stem),load('validation',args.stem)
    kinds=('source_port_dy16','target_port_dy16','source_port_dx8','target_port_dx8',
           'source_x_dy50','target_x_dy50','source_yphase_dy50','target_yphase_dy50',
           'source_port_target_x10','target_port_source_x10','source_family_yphase',
           'target_family_yphase','signed_dy_exact',
           'target_port_dy8','source_port_dy8','target_port_yphase20',
           'source_port_yphase20','target_port_x','source_port_x',
           'target_port_gap_y','source_port_gap_y','signed_dx_dybucket',
           'dy_phase_exact','port_pair_distance')
    baseline=score(val,kinds[0],{})
    results=[]
    for kind in kinds:
        for prior in (20,100):
            table=fit(dev,kind,prior)
            result={'kind':kind,'prior':prior,'entries':len(table),
                    'validation_score':score(val,kind,table)}
            results.append(result)
            print(result,flush=True)
    report={'baseline':baseline,'stem':args.stem,'candidates':results,'elapsed_seconds':time.monotonic()-start,
            'holdout_used':False}
    (ROOT/'reports'/f'V4-table-interactions-{args.stem}.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
