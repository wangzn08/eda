"""Development-fit route-aware challengers; validation only for comparison."""
import csv,json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_asymmetric_boundary import spatial
from experiment_v7_teacher import score
out=ROOT/'out/v117';start=time.monotonic()
p=np.loadtxt(out/'all.prediction.csv',delimiter=',',skiprows=1,usecols=2,dtype=np.int64);d=np.loadtxt(out/'all.descriptors.csv',delimiter=',',skiprows=1,dtype=np.float32)
x,y,_,_=load('development');v,yv,_,_=load('validation');n=len(y);b,bv=p[:n],p[n:];r,rv=d[:n],d[n:];assert len(bv)==len(yv)==150053
with (out/'development-base.csv').open() as f:baseline=np.array([int(a['delay']) for a in csv.DictReader(f)])
assert np.array_equal(b,baseline)
with (ROOT/'out/v116/profile/validation.csv').open() as f:baselinev=np.array([int(a['delay']) for a in csv.DictReader(f)])
assert np.array_equal(bv,baselinev)
np.savez(out/'route-data.npz',development=r,validation=rv,development_base=b,validation_base=bv)
def route_features(z,base,t):
 # Route fields and interactions depend on the predictor, not golden labels.
 a=spatial(z,base);s,tgt=t[:,0],t[:,1];phase=(t[:,6]+29)*71+t[:,7]+35
 extras=np.column_stack((t,s*160+tgt,s*4189+phase,tgt*4189+phase,s*480+(t[:,6]%10)*24+t[:,7]%24,tgt*480+(t[:,6]%10)*24+t[:,7]%24,t[:,8]*120+z[:,4]%10*12+z[:,5]%12,z[:,0]-t[:,10],z[:,1]-t[:,11],t[:,13]-base,t[:,12]==0))
 return np.column_stack((a,extras)).astype(np.float32)
a,av=route_features(x,b,r),route_features(v,bv,rv);np.savez(out/'fit-features.npz',a=a,av=av,y=y,yv=yv,b=b,bv=bv)
report={'state':'running','fit_split':'development','holdout_used':False,'base_score':score(yv,bv),'descriptor_predictions_match_v116':True,'scope':'Python prototype, throughput and runtime bytes not yet accepted','candidates':[]}
for name,leaves,trees,minleaf in [('control',127,64,30),('single1023',1023,1,20),('single8191',8191,1,20),('route16',255,16,30),('route64',127,64,30)]:
 inputs,valid=(spatial(x,b),spatial(v,bv)) if name=='control' else (a,av)
 ds=lgb.Dataset(inputs,label=(y-b),weight=1000/np.maximum(y,1))
 m=lgb.train({'objective':'regression_l1','learning_rate':1 if trees==1 else .15,'num_leaves':leaves,'min_data_in_leaf':minleaf,'num_threads':1,'verbosity':-1,'force_col_wise':True,'seed':20261007,'deterministic':True},ds,num_boost_round=trees)
 m.save_model(str(out/f'{name}.txt'));pred=np.rint(np.maximum(0,bv+m.predict(valid,num_threads=1)));np.save(out/f'{name}.npy',pred);item={'name':name,'leaves':leaves,'trees':trees,'score':score(yv,pred),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V117-route-aware-models.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V117-route-aware-models.json').write_text(json.dumps(report,indent=2)+'\n')
