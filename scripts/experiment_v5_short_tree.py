"""Test whether an offline structural model helps hard short routes."""
import csv
import json
import time

import lightgbm as lgb
import numpy as np

from architecture import ROOT
from v4_features import NAMES


def predictions(split):
    root=ROOT/'out/evaluation'
    with (root/f'{split}.v4-horizontal.csv').open(newline='') as f:
        return np.fromiter((int(r['delay']) for r in csv.DictReader(f)),dtype=np.float64)


def score(y,p):
    m=y>0
    return float(np.mean(100*(1-np.tanh(4*np.abs(y[m]-p[m])/y[m])),dtype=np.float64))


def main():
    start=time.monotonic()
    root=ROOT/'out/evaluation'
    a=np.load(root/'development.v4-features.npz')
    b=np.load(root/'validation.v4-features.npz')
    x=a['x'].copy(); y=a['truth'].astype(np.float64); base=predictions('development')
    xv=b['x'].copy();yv=b['truth'].astype(np.float64);bv=predictions('validation')
    x[:,NAMES.index('v3_delay')]=base
    xv[:,NAMES.index('v3_delay')]=bv
    gates={
        'all':np.ones(len(y),dtype=bool),
        'dy_lt_20':x[:,NAMES.index('abs_dy')]<20,
        'dy_lt_40':x[:,NAMES.index('abs_dy')]<40,
        'dx_lt_20':x[:,NAMES.index('abs_dx')]<20,
        'either_short':(x[:,NAMES.index('abs_dy')]<40)|(x[:,NAMES.index('abs_dx')]<20),
    }
    vgates={
        'all':np.ones(len(yv),dtype=bool),
        'dy_lt_20':xv[:,NAMES.index('abs_dy')]<20,
        'dy_lt_40':xv[:,NAMES.index('abs_dy')]<40,
        'dx_lt_20':xv[:,NAMES.index('abs_dx')]<20,
        'either_short':(xv[:,NAMES.index('abs_dy')]<40)|(xv[:,NAMES.index('abs_dx')]<20),
    }
    base_score=score(yv,bv)
    results=[]
    importances={}
    for trained_on in ('all','dy_lt_40','either_short'):
        m=gates[trained_on]&(y>0)&(base>0)
        label=(y[m]-base[m])/base[m]
        ds=lgb.Dataset(x[m],label=label,feature_name=list(NAMES))
        model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':0.07,
                         'num_leaves':31,'max_depth':6,'min_data_in_leaf':100,
                         'num_threads':2,'force_col_wise':True,'deterministic':True,
                         'seed':20261004},ds,num_boost_round=64)
        model_dir=ROOT/'out/v5';model_dir.mkdir(parents=True,exist_ok=True)
        model.save_model(str(model_dir/f'{trained_on}.txt'))
        importances[trained_on]=sorted(zip(NAMES,map(int,model.feature_importance('gain'))),
                                     key=lambda z:z[1],reverse=True)
        for trees in (8,16,24,32,48,64):
            residual=model.predict(xv,num_iteration=trees,num_threads=2)
            raw=np.rint(np.maximum(0,bv*(1+residual)))
            for applied_to in ('all','dy_lt_20','dy_lt_40','dx_lt_20','either_short'):
                pred=np.where(vgates[applied_to],raw,bv)
                results.append({'trained_on':trained_on,'trees':trees,
                                'applied_to':applied_to,'validation_score':score(yv,pred),
                                'active_fraction':float(vgates[applied_to].mean())})
        print(trained_on,max((r for r in results if r['trained_on']==trained_on),
                             key=lambda z:z['validation_score']),flush=True)
    report={'baseline':base_score,'best':max(results,key=lambda z:z['validation_score']),
            'candidates':results,'feature_gain_importance':importances,
            'elapsed_seconds':time.monotonic()-start,
            'holdout_used':False}
    (ROOT/'reports/V5-short-tree-research.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'baseline':base_score,'best':report['best'],
                      'elapsed_seconds':report['elapsed_seconds']},indent=2),flush=True)


if __name__=='__main__':main()
