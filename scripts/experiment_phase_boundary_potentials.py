"""Phase-conditioned physical potential residuals; development fitting only."""
import json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from boundary_potential_features import potentials
from phase_boundary_potential_features import phase_potentials
from curve_response_features import features
z=np.load(ROOT/'out/v125/fit-features.npz');folder=ROOT/'out/v197';folder.mkdir(exist_ok=True)
a=np.column_stack((features(z['a']),potentials(z['a']),phase_potentials(z['a']))).astype(np.float32)
av=np.column_stack((features(z['av']),potentials(z['av']),phase_potentials(z['av']))).astype(np.float32)
report={'state':'running','fit_scope':'development residual with phase-conditioned architecture-only Bellman penalties','holdout_used':False,'features':a.shape[1],'candidates':[]}
for name,leaves,trees in [('large',511,256),('wide',1023,512)]:
    start=time.monotonic();ds=lgb.Dataset(a,label=z['y']-z['b'],weight=1000/np.maximum(z['y'],1))
    model=lgb.train({'objective':'regression_l1','num_leaves':leaves,'min_data_in_leaf':30,'learning_rate':.07,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261008},ds,num_boost_round=trees)
    model.save_model(str(folder/f'{name}.txt'));p=np.rint(np.maximum(0,z['bv']+model.predict(av,num_threads=1)));np.save(folder/f'{name}.npy',p)
    item={'name':name,'score':float(100*np.mean(1-np.tanh(4*np.abs(p-z['yv'])/z['yv']))),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True)
    (ROOT/'reports/V197-phase-boundary-residual.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V197-phase-boundary-residual.json').write_text(json.dumps(report,indent=2)+'\n')
