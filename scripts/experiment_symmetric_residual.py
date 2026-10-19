"""Independent symmetric-tree architecture, with ordered categorical statistics.

No validation labels are supplied to training or CTR construction. This is a
fixed iteration research screen, not a frozen standard runtime result.
"""
import json,time
import numpy as np
from catboost import CatBoostRegressor,Pool
from architecture import ROOT
from native_research_labels import load_labels
from experiment_v7_teacher import score

out=ROOT/'out/v256';out.mkdir(exist_ok=True)
z=load_labels();y,yv=z['y'].astype(float),z['yv'].astype(float);n,nv=len(y),len(yv)
x=np.memmap(ROOT/'out/v243/all.features.f32',mode='r',dtype='<f4',shape=(n+nv,137));base=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4').astype(float);b,bv=base[:n],base[n:]
report={'state':'running','fit_scope':'development only; no validation eval set or categorical label access','holdout_used':False,'reference':'https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html','candidates':[]}
for name,depth,categorical in [('numeric-d8',8,False),('ordered-category-d8',8,True),('numeric-d10',10,False)]:
 start=time.monotonic();data=np.asarray(x)
 cats=[]
 if categorical:
  cats=[7,8,9,10,11,12,13,14,15,16,17,18];data=data.astype(object)
  for k in cats:data[:,k]=x[:,k].astype(np.int32).astype(str)
 train=Pool(data[:n],label=y-b,weight=1000/np.maximum(y,1),cat_features=cats);valid=Pool(data[n:],cat_features=cats)
 model=CatBoostRegressor(iterations=512,depth=depth,learning_rate=.12,loss_function='MAE',thread_count=1,random_seed=20261019,verbose=128,allow_writing_files=False,l2_leaf_reg=5,one_hot_max_size=16,max_ctr_complexity=2)
 model.fit(train);model.save_model(str(out/f'{name}.cbm'));model.save_model(str(out/f'{name}.json'),format='json')
 for trees in (64,128,256,512):
  p=np.rint(np.maximum(0,bv+model.predict(valid,ntree_end=trees,thread_count=1)));np.save(out/f'{name}-{trees}.npy',p)
  item={'name':name,'depth':depth,'trees':trees,'score':score(yv,p),'exact_fraction':float(np.mean(p==yv)),'elapsed_seconds':time.monotonic()-start,'model_bytes':(out/f'{name}.cbm').stat().st_size};report['candidates'].append(item);print(json.dumps(item),flush=True)
  (ROOT/'reports/V256-symmetric-residual.json').write_text(json.dumps(report,indent=2)+'\n')
 del data,train,valid,model
report['state']='complete';report['best']=max(report['candidates'],key=lambda v:v['score']);(ROOT/'reports/V256-symmetric-residual.json').write_text(json.dumps(report,indent=2)+'\n')
