"""Compare categorical endpoint treatment with the numeric residual teacher."""
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
    # Signed categorical values must be nonnegative for LightGBM.
    x[:,14:16]+=1;xv[:,14:16]+=1
    cats=[10,11,12,13,14,15,22]
    ds=lgb.Dataset(x[m],label=(y[m]-b[m])/b[m],feature_name=list(NAMES),categorical_feature=cats)
    model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':.05,
                     'num_leaves':127,'max_depth':-1,'min_data_in_leaf':80,
                     'cat_smooth':20,'cat_l2':10,'max_cat_to_onehot':4,
                     'num_threads':2,'force_col_wise':True,'deterministic':True,
                     'seed':20261004},ds,num_boost_round=2048)
    model.save_model(str(ROOT/'out/v7/l1-categorical.txt'))
    results=[]
    for trees in (256,512,768,1024,1536,2048):
        correction=model.predict(xv,num_iteration=trees,num_threads=2)
        pred=np.rint(np.maximum(0,bv*(1+correction)))
        item={'trees':trees,'validation_score':score(yv,pred)};results.append(item);print(item,flush=True)
    (ROOT/'reports/V7-categorical-research.json').write_text(json.dumps({'baseline':score(yv,bv),
        'best':max(results,key=lambda z:z['validation_score']),'candidates':results,
        'categorical_indices':cats,'sign_offset':1,'holdout_used':False,
        'elapsed_seconds':time.monotonic()-start},indent=2)+'\n')

if __name__=='__main__':main()
