"""Extend the strongest development-trained residual model and select on validation."""
import json
import time
import lightgbm as lgb
import numpy as np
from architecture import ROOT
from v4_features import NAMES
from experiment_v7_teacher import load,score

def main():
    start=time.monotonic();x,y,b=load('development');xv,yv,bv=load('validation')
    m=(y>0)&(b>0)
    ds=lgb.Dataset(x[m],label=(y[m]-b[m])/b[m],feature_name=list(NAMES),free_raw_data=False)
    base=lgb.Booster(model_file=str(ROOT/'out/v7/l1-127.txt'))
    model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':.05,
                     'num_leaves':127,'max_depth':-1,'min_data_in_leaf':80,
                     'num_threads':2,'force_col_wise':True,'deterministic':True,
                     'seed':20261004},ds,num_boost_round=1536,init_model=base)
    model.save_model(str(ROOT/'out/v7/l1-127-extended.txt'))
    results=[]
    for trees in (512,768,1024,1280,1536,1792,2048):
        residual=model.predict(xv,num_iteration=trees,num_threads=2)
        for blend in (.75,1.):
            pred=np.rint(np.maximum(0,bv*(1+blend*residual)))
            results.append({'trees':trees,'blend':blend,'validation_score':score(yv,pred)})
        print(results[-1],flush=True)
    report={'baseline':score(yv,bv),'best':max(results,key=lambda z:z['validation_score']),
            'candidates':results,'model':'out/v7/l1-127-extended.txt','holdout_used':False,
            'elapsed_seconds':time.monotonic()-start}
    (ROOT/'reports/V7-extended-research.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
