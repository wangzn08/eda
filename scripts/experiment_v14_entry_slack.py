"""Learn optimality slack from independently generated feasible route bounds."""
import csv,json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from experiment_v7_teacher import load,score
from v4_features import NAMES
from v9_topology_features import EXTRA_NAMES
from v10_wire_features import WIRE_NAMES,augment_wire
BOUND_NAMES=('route_upper_bound','bound_available','bound_to_v6_ratio','bound_minus_v6')

def data(split):
    x,y,b=load(split);x=augment_wire(x)
    path=ROOT/'out/evaluation'/f'{split}.v13-bound.csv'
    with path.open() as f:
        rows=list(csv.DictReader(f));u=np.array([int(r['delay']) for r in rows],dtype=np.float64)
    with (ROOT/'out/evaluation'/f'{split}.request.csv').open() as f:
        requests=list(csv.DictReader(f))
    if len(rows)!=len(y) or any((r['From'],r['To'])!=(q['From'],q['To']) for r,q in zip(rows,requests)):raise ValueError('Bound rows differ')
    valid=u<100000000
    if np.any(u[valid]<y[valid]):raise ValueError('Invalid upper bound')
    anchor=np.where(valid,u,b)
    x=np.column_stack((x,np.where(valid,u,0),valid,np.where(valid,u/np.maximum(b,1),0),np.where(valid,u-b,0))).astype(np.float32)
    return x,y,b,anchor,np.where(valid,u,np.inf),valid

def main():
    start=time.monotonic();x,y,b,anchor,u,valid=data('development');xv,yv,bv,av,uv,vv=data('validation')
    names=list(NAMES+EXTRA_NAMES+WIRE_NAMES+BOUND_NAMES);folder=ROOT/'out/v14';folder.mkdir(parents=True,exist_ok=True);results=[]
    for use_slack in (False,True):
        base=anchor if use_slack else b;vbase=av if use_slack else bv
        # Keep the original baseline as a feature; only the regression anchor changes.
        mask=(y>0)&(base>0)
        ds=lgb.Dataset(x[mask],label=(y[mask]-base[mask])/base[mask],feature_name=names,free_raw_data=False)
        model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':.05,'num_leaves':127,
             'min_data_in_leaf':40,'num_threads':2,'force_col_wise':True,'deterministic':True,'seed':20261004},ds,num_boost_round=1536)
        model_path=folder/f'slack-{int(use_slack)}.txt';model.save_model(str(model_path))
        for trees in (512,1024,1536):
            pred=np.rint(np.maximum(0,vbase*(1+model.predict(xv,num_iteration=trees,num_threads=2))))
            pred=np.minimum(pred,uv)
            result={'slack_anchor':use_slack,'trees':trees,'validation_score':score(yv,pred),
             'covered_score':score(yv[vv],pred[vv]),'uncovered_score':score(yv[~vv],pred[~vv]),'model':str(model_path.relative_to(ROOT))}
            results.append(result);print(json.dumps(result),flush=True)
        np.save(folder/f'validation-{int(use_slack)}.npy',pred)
    report={'fit_split':'development','holdout_used':False,'features':names,'bound_generation_used_labels':False,
      'development_bounds':int(valid.sum()),'validation_bounds':int(vv.sum()),'upper_bound_violations':0,
      'candidates':results,'best':max(results,key=lambda r:r['validation_score']),'elapsed_seconds':time.monotonic()-start}
    (ROOT/'reports/V14-entry-slack-research.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
