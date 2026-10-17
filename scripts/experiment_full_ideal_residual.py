"""Exact finite ideal baseline plus physical boundary calibration.
Architecture distances are generated without golden labels. Only development
golden residuals are fitted; validation predictions are evaluated after fitting.
"""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from boundary_potential_features import potentials
from curve_response_features import features
z=np.load(ROOT/'out/v125/fit-features.npz');folder=ROOT/'out/v200';folder.mkdir(exist_ok=True)
p=np.fromfile(ROOT/'out/v198/ideal.predictions.i32',dtype='<i4').astype(np.float32)
n=len(z['y']);assert len(p)==n+len(z['yv']);b,bv=p[:n],p[n:]
def prepare(a,full,base):
    return np.column_stack((features(a),potentials(a),full,full-base,(full-base)/np.maximum(full,1))).astype(np.float32)
a=prepare(z['a'],b,z['b']);av=prepare(z['av'],bv,z['bv'])
def score(p):return float(100*np.mean(1-np.tanh(4*np.abs(p-z['yv'])/z['yv'])))
report={'state':'running','fit_scope':'development golden residual over full finite ideal architecture distances and physical boundary features','holdout_used':False,'features':a.shape[1],'base_validation_score':score(bv),'scope':'Accuracy prototype, native memory/storage/time not established','candidates':[]}
for name,leaves,trees in [('compact',127,64),('large',511,256),('wide',1023,512)]:
    start=time.monotonic();ds=lgb.Dataset(a,label=z['y']-b,weight=1000/np.maximum(z['y'],1))
    model=lgb.train({'objective':'regression_l1','num_leaves':leaves,'min_data_in_leaf':30,'learning_rate':.07,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261008},ds,num_boost_round=trees)
    model.save_model(str(folder/f'{name}.txt'));q=np.rint(np.maximum(0,bv+model.predict(av,num_threads=1)));np.save(folder/f'{name}.npy',q)
    item={'name':name,'score':score(q),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True)
    (ROOT/'reports/V200-full-ideal-residual.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V200-full-ideal-residual.json').write_text(json.dumps(report,indent=2)+'\n')
