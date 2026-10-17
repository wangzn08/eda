"""Fit a compact residual student with architecture-generated exact supervision."""
import csv,json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from v4_features import FeatureBuilder
from v10_wire_features import augment_wire
from experiment_asymmetric_boundary import spatial
from experiment_v7_teacher import score
folder=ROOT/'out/v163';start=time.monotonic();z=np.load(ROOT/'out/v125/fit-features.npz')
with (folder/'teacher.golden.csv').open() as f:rows=list(csv.DictReader(f))
with (folder/'teacher.prediction.csv').open() as f:pred=list(csv.DictReader(f))
assert len(rows)==len(pred) and all((a['From'],a['To'])==(b['From'],b['To']) for a,b in zip(rows,pred))
y=np.array([int(r['delay']) for r in rows],dtype=np.float32);b=np.array([int(r['delay']) for r in pred],dtype=np.float32)
builder=FeatureBuilder();x=np.array([builder.build(r['From'],r['To'],base) for r,base in zip(rows,b)],dtype=np.float32);x=augment_wire(x)
r=np.loadtxt(folder/'teacher.descriptors.csv',delimiter=',',skiprows=1,dtype=np.float32);assert r.shape==(len(rows),22)
curvature=r[:,17]-r[:,16]-4*(r[:,16]-r[:,15]);extras=np.column_stack((r,curvature,r[:,18]-r[:,17],r[:,15]-12.5*np.abs(r[:,6])-125/12*np.abs(r[:,7]),r[:,19]*np.maximum(0,r[:,4]-1),r[:,20]*np.minimum(r[:,4]/5,r[:,5]/6),r[:,0]//8,r[:,1]//8,(r[:,0]-r[:,1])%8,r[:,12]==0,r[:,15]==r[:,18],r[:,2]%10,r[:,3]%12))
a=np.column_stack((spatial(x,b),extras)).astype(np.float32);assert a.shape[1]==133
np.savez(folder/'teacher.features.npz',a=a,y=y,b=b)
report={'state':'running','fit_split':'development plus architecture-generated samples','holdout_used':False,'teacher_rows':len(y),'teacher_base_score':score(y,b),'scope':'Accuracy student prototype; native inference and paired timing pending','candidates':[]}
for multiplier in (.25,1):
 ds=lgb.Dataset(np.vstack((z['a'],a)),label=np.concatenate((z['y']-z['b'],y-b)),weight=np.concatenate((1000/np.maximum(z['y'],1),multiplier*1000/np.maximum(y,1))))
 m=lgb.train({'objective':'regression_l1','num_leaves':511,'min_data_in_leaf':30,'learning_rate':.07,'num_threads':1,'verbosity':-1,'deterministic':True,'force_col_wise':True,'seed':20261007},ds,num_boost_round=256);name=f'weight-{multiplier}';m.save_model(str(folder/f'{name}.txt'))
 p=np.rint(np.maximum(0,z['bv']+m.predict(z['av'],num_threads=1)));np.save(folder/f'{name}.npy',p)
 item={'name':name,'score':score(z['yv'],p),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V163-architecture-supervision.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V163-architecture-supervision.json').write_text(json.dumps(report,indent=2)+'\n')
