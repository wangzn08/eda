"""Residual calibration after real two-step expansion; development fit only."""
import csv,json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from curve_response_features import features
from experiment_v7_teacher import score
z=np.load(ROOT/'out/v125/fit-features.npz');folder=ROOT/'out/v175';folder.mkdir(exist_ok=True)
with (folder/'physical.prediction.csv').open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)],np.float32)
n=len(z['y']);assert len(p)==n+len(z['yv']);b,bv=p[:n],p[n:];reference=np.loadtxt(ROOT/'out/v173/validation/h8-depth2.csv',delimiter=',',skiprows=1,usecols=2,dtype=np.float32);assert np.array_equal(bv,reference)
a=np.column_stack((features(z['a']),b,b-z['b'],(b-z['b'])/np.maximum(b,1))).astype(np.float32);av=np.column_stack((features(z['av']),bv,bv-z['bv'],(bv-z['bv'])/np.maximum(bv,1))).astype(np.float32)
start=time.monotonic();report={'state':'running','fit_split':'development','holdout_used':False,'base_validation_score':score(z['yv'],bv),'scope':'Two-step physical teacher plus residual, accuracy prototype; pruning/distillation and native timing pending','candidates':[]}
for name,leaves,trees in [('compact',511,256),('wide',1023,512)]:
 ds=lgb.Dataset(a,label=z['y']-b,weight=1000/np.maximum(z['y'],1));m=lgb.train({'objective':'regression_l1','num_leaves':leaves,'min_data_in_leaf':30,'learning_rate':.07,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261008},ds,num_boost_round=trees);m.save_model(str(folder/f'{name}.txt'))
 q=np.rint(np.maximum(0,bv+m.predict(av,num_threads=1)));np.save(folder/f'{name}.npy',q);item={'name':name,'score':score(z['yv'],q),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V175-physical-prefix-residual.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V175-physical-prefix-residual.json').write_text(json.dumps(report,indent=2)+'\n')
