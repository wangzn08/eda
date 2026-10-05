"""Categorical endpoint relations via CatBoost; labels from development only."""
import json,time
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor,Pool
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
from v4_features import NAMES
from v9_topology_features import EXTRA_NAMES
from v10_wire_features import WIRE_NAMES
from experiment_v14_entry_slack import BOUND_NAMES

def frame(x):
    f=pd.DataFrame(x,columns=list(NAMES+EXTRA_NAMES+WIRE_NAMES+BOUND_NAMES))
    cats=['source_port','target_port','source_family','target_family','route_class']
    for name in cats:f[name]=f[name].astype(int).astype(str)
    f['port_pair']=(x[:,10].astype(int)*496+x[:,11].astype(int)).astype(str);cats+=['port_pair']
    f['direction_class']=((x[:,14]+1)*3+x[:,15]+1).astype(int).astype(str);cats+=['direction_class']
    return f,cats

def main():
    start=time.monotonic();folder=ROOT/'out/v20';folder.mkdir(exist_ok=True)
    x,y,b,u=load('development');xv,yv,bv,uv=load('validation');f,cats=frame(x);fv,_=frame(xv);m=(y>0)&(b>0)
    train=Pool(f.loc[m],label=100*(y[m]-b[m])/b[m],weight=b[m]/y[m],cat_features=cats)
    results=[];prior=np.load(ROOT/'out/v19/validation-1536.npy')
    for depth in (6,8):
        model=CatBoostRegressor(iterations=2048,depth=depth,learning_rate=.06,loss_function='MAE',thread_count=2,
            random_seed=20261005,l2_leaf_reg=5,verbose=256,max_ctr_complexity=2,allow_writing_files=False)
        model.fit(train)
        path=folder/f'categorical-{depth}.cbm';model.save_model(str(path))
        for trees in (512,1024,1536,2048):
            raw=np.maximum(0,bv*(1+model.predict(fv,ntree_end=trees,thread_count=2)/100))
            pred=np.minimum(np.rint(raw),uv)
            for w in (0.,.25,.5,.75):
                blend=np.minimum(np.rint((1-w)*pred+w*prior),uv)
                result={'depth':depth,'trees':trees,'v19_weight':w,'validation_score':score(yv,blend),
                    'model':str(path.relative_to(ROOT)),'model_bytes':path.stat().st_size}
                results.append(result);print(json.dumps(result),flush=True)
                np.save(folder/f'validation-{depth}-{trees}-{w}.npy',blend)
        report={'fit_split':'development','holdout_used':False,'baseline':score(yv,prior),'categorical_features':cats,
            'candidates':results,'best':max(results,key=lambda z:z['validation_score']),'elapsed_seconds':time.monotonic()-start}
        (ROOT/'reports/V20-categorical-architecture.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
