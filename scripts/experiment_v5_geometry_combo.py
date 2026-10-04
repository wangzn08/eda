"""Fit candidate column and geometry residual tables after V4."""
import json
import time

from architecture import ROOT
from experiment_region_port import load
from experiment_v4_interactions import fit,key,score


def apply(rows,kind,table):
    return [(*row[:7],max(0,round(row[7]+table.get(key(row,kind),0)))) for row in rows]


def main():
    start=time.monotonic()
    dev=load('development','v4-horizontal')
    val=load('validation','v4-horizontal')
    orders=(
        ('source_x_target_x','target_x_dx16','source_port_x'),
        ('target_x_dx16','source_x_target_x','source_port_x'),
        ('source_port_x','source_x_target_x','target_x_dx16'),
        ('source_x_target_x','source_port_x','source_yphase_dx16'),
        ('source_x_target_x','target_x_dx16','source_yphase_dx16','target_yphase_dx16'),
        ('source_x_target_x','source_port_x','source_yphase_dx16','target_yphase_dx16','target_x_dx16'),
        ('source_port_x','source_x_target_x','source_yphase_dx16','target_yphase_dx16','target_x_dx16'),
    )
    results=[]
    for order in orders:
        training,validation=dev,val
        stages=[]
        for kind in order:
            table=fit(training,kind,20)
            training=apply(training,kind,table)
            validation=apply(validation,kind,table)
            stages.append({'kind':kind,'entries':len(table),
                           'validation_score':score(validation,kind,{})})
        results.append({'order':order,'stages':stages})
        print(results[-1],flush=True)
    report={'baseline':score(val,'source_x_target_x',{}),
            'candidates':results,'elapsed_seconds':time.monotonic()-start,
            'holdout_used':False}
    (ROOT/'reports/V5-geometry-combo.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
