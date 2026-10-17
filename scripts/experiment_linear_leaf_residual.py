"""Piecewise affine residual response, development fit/full validation screen."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');out=ROOT/'out/v160';out.mkdir(exist_ok=True);start=time.monotonic();r={'state':'running','fit_split':'development','holdout_used':False,'scope':'Linear-leaf accuracy prototype; packed/native inference pending','reference':'LightGBM linear_tree official documentation; adapted intrinsic residual fields','candidates':[]}
for relative in (False,True):
 target=z['y']-z['b'];weight=1/np.maximum(z['y'],1)
 if relative:target=target/np.maximum(z['b'],1);weight=np.ones(len(target))
 for leaves,trees in ((63,1),(255,1),(511,1),(63,32)):
  name=f'rel{int(relative)}-leaves{leaves}-trees{trees}';ds=lgb.Dataset(z['a'],label=target,weight=weight,params={'linear_tree':True});m=lgb.train({'objective':'regression','learning_rate':1 if trees==1 else .08,'linear_tree':True,'linear_lambda':1,'num_leaves':leaves,'min_data_in_leaf':100,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007},ds,num_boost_round=trees);m.save_model(str(out/f'{name}.txt'));q=m.predict(z['av'],num_threads=1)
  if relative:q=q*z['bv']
  pred=np.rint(np.maximum(0,z['bv']+q));np.save(out/(name+'.npy'),pred);item={'name':name,'score':score(z['yv'],pred),'model_bytes':(out/f'{name}.txt').stat().st_size,'elapsed_seconds':time.monotonic()-start};r['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V160-linear-leaf-residual.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports/V160-linear-leaf-residual.json').write_text(json.dumps(r,indent=2)+'\n')
