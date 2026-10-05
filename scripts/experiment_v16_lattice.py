"""Architecture lattice interaction features and relative-error-weighted residuals."""
import json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from experiment_v14_entry_slack import data,BOUND_NAMES
from experiment_v7_teacher import score
from v4_features import NAMES
from v9_topology_features import EXTRA_NAMES
from v10_wire_features import WIRE_NAMES
NEW_NAMES=('joint_remainder_10_12','joint_remainder_4_4','signed_remainder_class',
 'horizontal_long_hops','vertical_long_hops','hop_balance','source_phase_10_12','target_phase_10_12',
 'port_pair','family_pair','source_boundary_phase','target_boundary_phase','adjusted_manhattan',
 'axis_minimum','axis_maximum','distance_over_bound','bound_gap_fraction')

def augment(x,b,u):
    names=list(NAMES+EXTRA_NAMES+WIRE_NAMES+BOUND_NAMES);i={n:k for k,n in enumerate(names)}
    rx=x[:,i['remaining_dx']];ry=x[:,i['remaining_dy']];ax=np.abs(rx);ay=np.abs(ry)
    hx=np.floor(ax/10);hy=np.floor(ay/12)
    cols=[(ax%10)*12+ay%12,(ax%4)*4+ay%4,(rx>0)*2+(ry>0),hx,hy,hx-hy,
      x[:,16]*12+x[:,18],x[:,17]*12+x[:,19],x[:,10]*496+x[:,11],x[:,12]*100+x[:,13],
      x[:,29]%12,x[:,30]%12,ax+ay,np.minimum(ax,ay),np.maximum(ax,ay),
      np.where(np.isfinite(u),(ax+ay)/np.maximum(np.where(np.isfinite(u),u,1),1),0),
      np.where(np.isfinite(u),(np.where(np.isfinite(u),u,0)-b)/np.maximum(b,1),0)]
    return np.column_stack((x,*cols)).astype(np.float32)

def main():
    start=time.monotonic();folder=ROOT/'out/v16';folder.mkdir(exist_ok=True)
    x,y,b,a,u,v=data('development');xv,yv,bv,av,uv,vv=data('validation');x=augment(x,b,u);xv=augment(xv,bv,uv)
    names=list(NAMES+EXTRA_NAMES+WIRE_NAMES+BOUND_NAMES+NEW_NAMES)
    prior=np.load(ROOT/'out/v14/validation-0.npy');results=[]
    report={'fit_split':'development','holdout_used':False,'baseline_score':score(yv,prior),
        'features':names,'hypothesis':'joint long-wire residue phases and endpoint interactions explain medium-range residuals',
        'candidates':results,'lightgbm_version':lgb.__version__}
    def save():
        report['elapsed_seconds']=time.monotonic()-start
        if results:report['best']=max(results,key=lambda z:z['validation_score'])
        (ROOT/'reports/V16-lattice-research.json').write_text(json.dumps(report,indent=2)+'\n')
    mask=(y>0)&(b>0)
    for leaves,weighted,rounds in ((127,True,3072),(255,True,2048)):
        ds=lgb.Dataset(x[mask],label=(y[mask]-b[mask])/b[mask],weight=b[mask]/y[mask] if weighted else None,
          feature_name=names,free_raw_data=False)
        model=lgb.train({'objective':'regression_l1','verbosity':-1,'learning_rate':.04,'num_leaves':leaves,
          'min_data_in_leaf':24,'num_threads':2,'force_col_wise':True,'deterministic':True,'seed':20261005},ds,num_boost_round=rounds,
          callbacks=[lgb.log_evaluation(512)])
        path=folder/f'lattice-{leaves}.txt';model.save_model(str(path))
        for trees in (512,1024,1536,2048,3072):
            if trees>rounds:continue
            pred=np.minimum(np.rint(np.maximum(0,bv*(1+model.predict(xv,num_iteration=trees,num_threads=2)))),uv)
            medium=(xv[:,8]>=25)&(xv[:,8]<150)
            item={'leaves':leaves,'trees':trees,'weighted':weighted,'validation_score':score(yv,pred),
              'medium_distance_score':score(yv[medium],pred[medium]),'uncovered_score':score(yv[~vv],pred[~vv]),
              'model':str(path.relative_to(ROOT)),'model_text_bytes':path.stat().st_size}
            results.append(item);save();print(json.dumps(item),flush=True)
            np.save(folder/f'validation-{leaves}-{trees}.npy',pred)
        report.setdefault('feature_importance',{})[str(leaves)]=sorted(zip(names,map(float,model.feature_importance('gain'))),key=lambda t:t[1],reverse=True)[:25]
        save()
    print(json.dumps(report['best']),flush=True)

if __name__=='__main__':main()
