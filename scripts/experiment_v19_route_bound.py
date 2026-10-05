"""Controlled retraining with tighter architecture-derived route bounds."""
import csv,json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from experiment_v14_entry_slack import data,BOUND_NAMES
from experiment_v7_teacher import score
from v4_features import NAMES
from v9_topology_features import EXTRA_NAMES
from v10_wire_features import WIRE_NAMES

def improved_data(split):
    x,y,b,a,u,v=data(split)
    with (ROOT/f'out/evaluation/{split}.v18-bound.csv').open() as f:rows=list(csv.DictReader(f))
    with (ROOT/f'out/evaluation/{split}.request.csv').open() as f:requests=list(csv.DictReader(f))
    assert len(rows)==len(y)
    assert all((a['From'],a['To'])==(b['From'],b['To']) for a,b in zip(rows,requests))
    upper=np.array([int(r['delay']) for r in rows],dtype=np.float64);valid=upper<100000000
    assert np.all(upper[valid]>=y[valid])
    x[:,73]=np.where(valid,upper,0);x[:,74]=valid;x[:,75]=np.where(valid,upper/np.maximum(b,1),0);x[:,76]=np.where(valid,upper-b,0)
    return x,y,b,np.where(valid,upper,np.inf)

def main():
    start=time.monotonic();folder=ROOT/'out/v19';folder.mkdir(exist_ok=True)
    x,y,b,u=improved_data('development');xv,yv,bv,uv=improved_data('validation');m=(y>0)&(b>0)
    names=list(NAMES+EXTRA_NAMES+WIRE_NAMES+BOUND_NAMES)
    ds=lgb.Dataset(x[m],label=(y[m]-b[m])/b[m],feature_name=names,free_raw_data=False)
    def progress(env):
        if (env.iteration+1)%256==0:print(f"iteration {env.iteration+1} elapsed {time.monotonic()-start:.1f}",flush=True)
    model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':.05,'num_leaves':127,
      'min_data_in_leaf':40,'num_threads':2,'force_col_wise':True,'deterministic':True,'seed':20261004},ds,num_boost_round=1536,callbacks=[progress])
    model.save_model(str(folder/'route-bound.txt'));results=[]
    for trees in (512,1024,1536):
        pred=np.minimum(np.maximum(0,np.rint(bv*(1+model.predict(xv,num_iteration=trees,num_threads=2)))),uv)
        r={'trees':trees,'validation_score':score(yv,pred),'model':'out/v19/route-bound.txt'};results.append(r)
        np.save(folder/f'validation-{trees}.npy',pred);print(json.dumps(r),flush=True)
    report={'fit_split':'development','holdout_used':False,'features':names,'baseline_v14':97.22350366143607,
      'baseline_v18_cap':97.35923802126318,'change':'Same V14 features and training parameters; replace route bound features by expanded certified hop enumeration.',
      'candidates':results,'best':max(results,key=lambda r:r['validation_score']),'elapsed_seconds':time.monotonic()-start}
    (ROOT/'reports/V19-route-bound-research.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
