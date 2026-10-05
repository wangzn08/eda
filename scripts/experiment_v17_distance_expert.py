"""Fit a dedicated short/medium-range expert, selected on validation only."""
import csv,json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from experiment_v14_entry_slack import data,BOUND_NAMES
from experiment_v16_lattice import augment,NEW_NAMES
from experiment_v7_teacher import score
from v4_features import NAMES
from v9_topology_features import EXTRA_NAMES
from v10_wire_features import WIRE_NAMES

def main():
    start=time.monotonic();folder=ROOT/'out/v17';folder.mkdir(exist_ok=True)
    x,y,b,a,u,v=data('development');xv,yv,bv,av,uv,vv=data('validation');x=augment(x,b,u);xv=augment(xv,bv,uv)
    prior_report=json.loads((ROOT/'reports/V16-lattice-research.json').read_text());best=prior_report['best']
    if best['validation_score']>prior_report['baseline_score']:
        prior=np.load(ROOT/f"out/v16/validation-{best['leaves']}-{best['trees']}.npy")
    else:prior=np.load(ROOT/'out/v14/validation-0.npy')
    with (ROOT/'out/evaluation/validation.v18-bound.csv').open() as f:
        uv=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
    uv=np.where(uv<100000000,uv,np.inf)
    prior=np.minimum(prior,uv)
    names=list(NAMES+EXTRA_NAMES+WIRE_NAMES+BOUND_NAMES+NEW_NAMES)
    m=(y>0)&(b>0)&(x[:,8]<150);vm=xv[:,8]<150;results=[]
    for mode in ('absolute','relative'):
        label=(y[m]-b[m]) if mode=='absolute' else (y[m]-b[m])/b[m]
        weight=1/y[m] if mode=='absolute' else b[m]/y[m]
        ds=lgb.Dataset(x[m],label=label,weight=weight/np.mean(weight),feature_name=names)
        def progress(env):
            if (env.iteration+1)%256==0:print(f"{mode} iteration {env.iteration+1} elapsed {time.monotonic()-start:.1f}",flush=True)
        model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':.05,'num_leaves':127,
          'min_data_in_leaf':20,'num_threads':2,'force_col_wise':True,'deterministic':True,'seed':20261005},ds,num_boost_round=2048,callbacks=[progress])
        path=folder/f'expert-{mode}.txt';model.save_model(str(path))
        for trees in (512,1024,1536,2048):
            corr=model.predict(xv[vm],num_iteration=trees,num_threads=2)
            value=bv[vm]+corr if mode=='absolute' else bv[vm]*(1+corr)
            expert=np.minimum(np.maximum(0,np.rint(value)),uv[vm]);pred=prior.copy();pred[vm]=expert
            item={'target':mode,'trees':trees,'validation_score':score(yv,pred),'expert_score':score(yv[vm],expert),
              'baseline_expert_score':score(yv[vm],prior[vm]),'model':str(path.relative_to(ROOT)),
              'model_text_bytes':path.stat().st_size};results.append(item)
            np.save(folder/f'validation-{mode}-{trees}.npy',pred);print(json.dumps(item),flush=True)
            report={'fit_split':'development','holdout_used':False,'routing_rule':'manhattan distance <150; no label-based gate',
              'baseline_model':'V16 255-leaf/2048-tree candidate capped by V18 bounds','baseline_score':score(yv,prior),'development_expert_rows':int(m.sum()),'validation_expert_rows':int(vm.sum()),
              'candidates':results,'best':max(results,key=lambda z:z['validation_score']),'elapsed_seconds':time.monotonic()-start}
            (ROOT/'reports/V17-distance-expert.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
