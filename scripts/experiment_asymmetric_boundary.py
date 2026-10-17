"""V100 asymmetric spatial residual trees, independently reproducible dev-only fit."""
import csv,json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features
from experiment_v7_teacher import score

def read(name):
 with (ROOT/'out/evaluation'/name).open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],np.float64)
def spatial(x,b):
 a=features(x,b);a[:,27]=x[:,1]%100;a[:,28]=x[:,3]%100
 z=[a]
 for cx,cy,p in [(x[:,0],x[:,1],x[:,10]),(x[:,2],x[:,3],x[:,11])]:
  z.append(np.column_stack([cx,119-cx,cy,549-cy,abs(cx-75),abs(cx-90),cy%100,49-cy%100,99-cy%100,p]))
  # Preserve discontinuities by explicit direction, distance, and phase joint codes.
  z.append(np.column_stack([p*120+(x[:,4]%10)*12+x[:,5]%12,p*100+cy%100,p*12+np.minimum(x[:,6]//10,11),p*46+np.minimum(x[:,7]//12,45)]))
 return np.column_stack(z).astype(np.float32)
def main():
 start=time.monotonic();out=ROOT/'out/v100';out.mkdir(exist_ok=True)
 x,y,_,_=load('development');v,yv,_,_=load('validation');b=read('development.v93-joint.csv');bv=read('validation.v93-base.csv');a=spatial(x,b);av=spatial(v,bv);mask=y>0
 report={'fit_split':'development','holdout_used':False,'scope':'Python asymmetric-tree prototype; not measured C++ submission','candidates':[]}
 for leaves in (31,127):
  ds=lgb.Dataset(a[mask],label=(y[mask]-b[mask])/100,weight=1000/np.maximum(y[mask],1))
  m=lgb.train({'objective':'regression_l1','learning_rate':.07,'num_leaves':leaves,'min_data_in_leaf':30,'num_threads':2,'verbosity':-1,'force_col_wise':True,'seed':20261007,'deterministic':True},ds,num_boost_round=512)
  m.save_model(str(out/f'boundary-{leaves}.txt'))
  for trees in (64,128,256,512):
   p=np.rint(np.maximum(0,bv+100*m.predict(av,num_iteration=trees,num_threads=2)));np.save(out/f'l{leaves}-t{trees}.npy',p)
   item={'leaves':leaves,'trees':trees,'score':score(yv,p),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True)
  (ROOT/'reports/V100-asymmetric-boundary.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=="__main__":main()
