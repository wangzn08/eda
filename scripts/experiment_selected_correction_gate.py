"""Development-trained shallow gates for omitting unnecessary residual work."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
out=ROOT/'out/v235';out.mkdir(exist_ok=True);f=np.load(ROOT/'out/v216/fit.npz');z=np.load(ROOT/'out/v125/fit-features.npz');m=lgb.Booster(model_file=str(ROOT/'out/v216/tree8.txt'));train=np.rint(np.maximum(0,f['b']+m.predict(f['a'],num_threads=1)));full=np.rint(np.maximum(0,f['bv']+m.predict(f['av'],num_threads=1)));delta=train-f['b'];features=list(range(69))+list(range(125,137));(out/'gate-features.json').write_text(json.dumps(features));a=f['a'][:,features];av=f['av'][:,features]
def score(p):return float(100*np.mean(1-np.tanh(4*abs(p-z['yv'])/z['yv'])))
r={'state':'running','fit_scope':'development only, label whether existing development-trained forest changes integer base','holdout_used':False,'full_score':score(full),'validation_nonzero_correction_fraction':float(np.mean(full!=f['bv'])),'candidates':[]}
for leaves,depth,penalty in [(15,5,1),(31,7,1),(63,8,1),(31,7,10),(63,8,10),(127,10,10)]:
 name=f'l{leaves}-w{penalty}';ds=lgb.Dataset(a,label=(delta!=0),weight=np.where(delta!=0,penalty,1));gate=lgb.train({'objective':'binary','num_leaves':leaves,'max_depth':depth,'min_data_in_leaf':100,'learning_rate':1,'num_threads':1,'verbosity':-1,'deterministic':True,'seed':20261008,'force_col_wise':True,'boost_from_average':False},ds,num_boost_round=1);gate.save_model(str(out/(name+'.txt')));prob=gate.predict(av,num_threads=1)
 for threshold in [.01,.03,.05,.1,.15,.2,.3,.5]:
  skip=prob<threshold;prediction=np.where(skip,f['bv'],full);item={'model':name,'threshold':threshold,'score':score(prediction),'skip_fraction':float(np.mean(skip)),'false_skip_fraction':float(np.mean(skip&(full!=f['bv'])))};r['candidates'].append(item)
 print(name,sorted([v for v in r['candidates'] if v['model']==name],key=lambda x:x['score'],reverse=True)[0],flush=True);(ROOT/'reports/V235-selected-correction-gate.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';eligible=[v for v in r['candidates'] if v['score']>=99.505];r['best_safe_screen']=max(eligible,key=lambda x:x['skip_fraction']) if eligible else None;(ROOT/'reports/V235-selected-correction-gate.json').write_text(json.dumps(r,indent=2)+'\n');print('best',r['best_safe_screen'],flush=True)
