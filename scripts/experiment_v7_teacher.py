"""Learn stronger V6 residual models; development fit, validation selection only."""
import csv
import json
import time
import lightgbm as lgb
import numpy as np
from architecture import ROOT
from v4_features import NAMES

def score(y,p):
    m=y>0
    return float(np.mean(100*(1-np.tanh(4*np.abs(y[m]-p[m])/y[m])),dtype=np.float64))

def load(split):
    root=ROOT/'out/evaluation'
    data=np.load(root/f'{split}.v4-features.npz')
    with (root/f'{split}.v6-pair.csv').open() as f:
        base=np.fromiter((int(r['delay']) for r in csv.DictReader(f)),dtype=np.float64)
    x=data['x'].copy();x[:,NAMES.index('v3_delay')]=base
    return x,data['truth'].astype(np.float64),base

def main():
    start=time.monotonic();x,y,b=load('development');xv,yv,bv=load('validation')
    m=(y>0)&(b>0)
    ds=lgb.Dataset(x[m],label=(y[m]-b[m])/b[m],feature_name=list(NAMES),free_raw_data=False)
    folder=ROOT/'out/v7';folder.mkdir(parents=True,exist_ok=True)
    results=[];importance={}
    for leaves in (31,63,127):
        model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':.05,
                         'num_leaves':leaves,'max_depth':-1,'min_data_in_leaf':80,
                         'num_threads':2,'force_col_wise':True,'deterministic':True,
                         'seed':20261004},ds,num_boost_round=512)
        model.save_model(str(folder/f'l1-{leaves}.txt'))
        importance[str(leaves)]=sorted(zip(NAMES,map(float,model.feature_importance('gain'))),key=lambda z:z[1],reverse=True)
        for trees in (32,64,128,256,384,512):
            correction=model.predict(xv,num_iteration=trees,num_threads=2)
            for blend in (.5,1.):
                pred=np.rint(np.maximum(0,bv*(1+blend*correction)))
                results.append({'leaves':leaves,'trees':trees,'blend':blend,'validation_score':score(yv,pred)})
        print(leaves,max((r for r in results if r['leaves']==leaves),key=lambda z:z['validation_score']),flush=True)
    report={'baseline':score(yv,bv),'best':max(results,key=lambda z:z['validation_score']),
            'candidates':results,'importance':importance,'holdout_used':False,'elapsed_seconds':time.monotonic()-start}
    (ROOT/'reports/V7-teacher-research.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['best'],flush=True)

if __name__=='__main__':main()
