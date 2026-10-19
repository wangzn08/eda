"""Development-trained selective inference for the wall-specialist residuals."""
import json
import lightgbm as lgb
import numpy as np
from architecture import ROOT
from selected_physics_interactions import augment

out=ROOT/'out/v248';out.mkdir(exist_ok=True)
z=np.load(ROOT/'out/v125/fit-features.npz');y,yv=z['y'],z['yv'];n,nv=len(y),len(yv)
x=np.memmap(ROOT/'out/v243/all.features.f32',mode='r',dtype='<f4',shape=(n+nv,137));base=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4').astype(float);train,valid=augment(x[:n]),augment(x[n:])
full=[]
for values,b in [(train,base[:n]),(valid,base[n:])]:
 correction=np.zeros(len(values))
 for i in (0,1):
  mask=(values[:,54]>0)==bool(i);model=lgb.Booster(model_file=str(ROOT/f'out/v244/wall-expert-{i}.txt'));correction[mask]=model.predict(values[mask],num_threads=1)
 full.append(np.rint(np.maximum(0,b+correction)))
label=full[0]!=base[:n]
def score(pred):return float(100*np.mean(1-np.tanh(4*abs(pred-yv)/yv)))
r={'state':'running','fit_scope':'development only; target whether trained expert changes rounded base','holdout_used':False,'full_score':score(full[1]),'candidates':[]}
for mode,features in [('geometry',list(range(69))+list(range(125,137))),('endpoint',list(range(69))+list(range(125,169)))]:
 (out/f'{mode}.features.json').write_text(json.dumps(features)+'\n')
 for leaves in (63,255):
  name=f'{mode}-{leaves}'
  gate=lgb.train({'objective':'binary','num_leaves':leaves,'max_depth':12,'min_data_in_leaf':100,'learning_rate':1,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019,'boost_from_average':False},lgb.Dataset(train[:,features],label=label),num_boost_round=1)
  gate.save_model(str(out/f'{name}.txt'));prob=gate.predict(valid[:,features],num_threads=1)
  for threshold in (.01,.03,.05,.1,.15,.2,.3,.5):
   skip=prob<threshold;pred=np.where(skip,base[n:],full[1]);item={'name':name,'mapping':f'out/v248/{mode}.features.json','model':f'out/v248/{name}.txt','threshold':threshold,'score':score(pred),'skip_fraction':float(np.mean(skip)),'false_skip_fraction':float(np.mean(skip&(full[1]!=base[n:])))};r['candidates'].append(item)
   np.save(out/f'{name}-t{threshold}.npy',pred)
  print(json.dumps({'model':name,'best':max([v for v in r['candidates'] if v['name']==name],key=lambda v:v['score'])}),flush=True)
  (ROOT/'reports/V248-domain-correction-gates.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';safe=[v for v in r['candidates'] if v['score']>=r['full_score']-.002];r['selected']=max(safe,key=lambda v:v['skip_fraction']);(ROOT/'reports/V248-domain-correction-gates.json').write_text(json.dumps(r,indent=2)+'\n');print('selected',json.dumps(r['selected']),flush=True)
