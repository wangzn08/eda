"""Fit compact residual tables in sequence after the frozen V3 estimator."""
import json
import time

from architecture import ROOT
from experiment_region_port import load
from experiment_v4_interactions import fit,key,score


def apply(rows,kind,table):
    return [(*row[:7],max(0,round(row[7]+table.get(key(row,kind),0)))) for row in rows]


def main():
    start=time.monotonic()
    dev,val=load('development','v3-final'),load('validation','v3-final')
    baseline=score(val,'signed_dy_exact',{})
    orders=(
        ('signed_dy_exact','target_port_dy16','source_port_dy16'),
        ('target_port_dy16','signed_dy_exact','source_port_dy16'),
        ('source_port_dy16','target_port_dy16','signed_dy_exact'),
    )
    candidates=[]
    for order in orders:
        training,validation=dev,val
        stages=[]
        for kind in order:
            table=fit(training,kind,20)
            training=apply(training,kind,table)
            validation=apply(validation,kind,table)
            stages.append({'kind':kind,'entries':len(table),
                           'validation_score':score(validation,kind,{})})
        candidates.append({'order':order,'stages':stages})
    report={'baseline':baseline,'candidates':candidates,
            'elapsed_seconds':time.monotonic()-start,'holdout_used':False}
    (ROOT/'reports/V4-table-combo.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
