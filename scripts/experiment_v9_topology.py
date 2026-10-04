"""Fit architecture-informed residual challengers on development labels only."""
import csv,json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from v4_features import NAMES
from v9_topology_features import EXTRA_NAMES,augment
from experiment_v7_teacher import load,score

def main():
    start=time.monotonic();x,y,b=load('development');xv,yv,bv=load('validation')
    x=augment(x);xv=augment(xv);names=list(NAMES+EXTRA_NAMES)
    mask=(y>0)&(b>0);folder=ROOT/'out/v9';folder.mkdir(parents=True,exist_ok=True)
    with (ROOT/'out/evaluation/validation.v8-cpp-v7.csv').open() as f:
        prior=np.fromiter((int(r['delay']) for r in csv.DictReader(f)),dtype=np.float64)
    with (ROOT/'out/evaluation/validation.v7-tree-dictionary16.csv').open() as f:
        assert len(list(csv.DictReader(f)))==len(yv)
    from experiment_local_oracle import LocalOracle
    oracle=LocalOracle(ROOT/'out/local-oracle/regular-16-dict.bin');bounds=np.full(len(yv),np.inf)
    with (ROOT/'out/evaluation/validation.request.csv').open() as f:
        for i,r in enumerate(csv.DictReader(f)):
            u,_=oracle.upper_bound(r['From'],r['To'])
            if u is not None:bounds[i]=u
    results=[]
    for weighted in (False,True):
        ds=lgb.Dataset(x[mask],label=(y[mask]-b[mask])/b[mask],
                       weight=np.clip(b[mask]/y[mask],.25,4) if weighted else None,
                       feature_name=names,free_raw_data=False)
        model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':.05,
             'num_leaves':127,'min_data_in_leaf':80,'num_threads':2,'force_col_wise':True,
             'deterministic':True,'seed':20261004},ds,num_boost_round=1536)
        path=folder/f'topology-{int(weighted)}.txt';model.save_model(str(path))
        for trees in (512,1024,1536):
            pred=np.rint(np.maximum(0,bv*(1+model.predict(xv,num_iteration=trees,num_threads=2))))
            clipped=np.minimum(pred,bounds)
            result={'weighted':weighted,'trees':trees,'score':score(yv,pred),'oracle_score':score(yv,clipped),'model':str(path.relative_to(ROOT))}
            results.append(result);print(json.dumps(result),flush=True)
        np.save(folder/f'validation-{int(weighted)}.npy',pred)
    report={'baseline_oracle_score':score(yv,prior),'features':names,'candidates':results,
      'best':max(results,key=lambda z:z['oracle_score']),'fit_split':'development','holdout_used':False,
      'elapsed_seconds':time.monotonic()-start}
    (ROOT/'reports/V9-topology-research.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
