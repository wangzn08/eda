"""Cost-weighted gate fitted to two-fold development-only expert comparisons."""
import csv,json,time,math
import numpy as np,lightgbm as lgb
from architecture import ROOT
from native_research_labels import load_labels
from experiment_v7_teacher import score

out=ROOT/'out/v262';out.mkdir(exist_ok=True)
z=load_labels();y,yv=z['y'].astype(float),z['yv'].astype(float);n=len(y)
x=np.load(ROOT/'out/v255/features.npy',mmap_mode='r');base=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4').astype(float);b,bv=base[:n],base[n:]
fold=np.random.default_rng(20261019).integers(0,2,n);oof_new=np.zeros(n);oof_old=np.zeros(n)
params={'objective':'regression_l1','learning_rate':.2,'num_leaves':511,'max_depth':24,'min_data_in_leaf':25,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019}
start=time.monotonic()
cached=(out/'oof.npz').exists()
for f in (() if cached else (0,1)):
 fit=fold!=f;check=fold==f
 for d in (0,1):
  ids=fit&((x[:n,54]>0)==bool(d));test=check&((x[:n,54]>0)==bool(d));ds=lgb.Dataset(x[:n][ids],label=(y-b)[ids],weight=1000/np.maximum(y[ids],1));m=lgb.train(params,ds,num_boost_round=32);oof_new[test]=b[test]+m.predict(x[:n][test],num_threads=1)
 ds=lgb.Dataset(x[:n,:137][fit],label=(y-b)[fit],weight=1000/np.maximum(y[fit],1));m=lgb.train({**params,'num_leaves':1023,'learning_rate':.3,'min_data_in_leaf':30},ds,num_boost_round=8);oof_old[check]=b[check]+m.predict(x[:n,:137][check],num_threads=1)
 print('fold',f,'seconds',time.monotonic()-start,flush=True)
if cached:
 saved=np.load(out/'oof.npz');assert np.array_equal(saved['fold'],fold);oof_new=saved['new'];oof_old=saved['old']
else:
 oof_new=np.rint(np.maximum(0,oof_new));oof_old=np.rint(np.maximum(0,oof_old));np.savez(out/'oof.npz',new=oof_new,old=oof_old,fold=fold)
gain=np.tanh(4*abs(oof_old-y)/np.maximum(y,1))-np.tanh(4*abs(oof_new-y)/np.maximum(y,1));mask=(abs(gain)>1e-12)&(y>0)
columns=list(range(69))+list(range(125,137));(out/'gate-features.json').write_text(json.dumps(columns)+'\n')
oldv=np.array([int(r['delay']) for r in csv.DictReader((ROOT/'out/v254/score-profile/validation.csv').open())]);newv=np.load(ROOT/'out/v255/wall-experts-32.npy')
report={'state':'running','fit_scope':'two-fold development-only cross-fitting of8-tree reference and32-tree/domain physical expert; weighted binary gain gate; full-data experts for validation','holdout_used':False,'oof_reference_uses_old_shallow_gate':False,'validation_fallback':'exact frozen V254 predictions, including old shallow gate','candidates':[]}
for leaves in (63,255,511):
 ds=lgb.Dataset(x[:n,:][:,columns][mask],label=gain[mask]>0,weight=abs(gain[mask]));gate=lgb.train({'objective':'binary','learning_rate':1,'num_leaves':leaves,'max_depth':12,'min_data_in_leaf':150,'num_threads':1,'verbosity':-1,'deterministic':True,'force_col_wise':True,'boost_from_average':False,'seed':20261019},ds,num_boost_round=1);gate.save_model(str(out/f'gain-{leaves}.txt'));prob=gate.predict(x[n:][:,columns],num_threads=1)
 for threshold in (.1,.2,.3,.4,.5,.6,.7,.8,.9,.95,.98):
  selected=prob>=threshold;p=np.where(selected,newv,oldv);path=f'gain-{leaves}-t{threshold:g}.npy';np.save(out/path,p)
  item={'leaves':leaves,'threshold':threshold,'score':score(yv,p),'physical_request_fraction':float(np.mean(selected)),'prediction':str((out/path).relative_to(ROOT))};report['candidates'].append(item);print(json.dumps(item),flush=True)
  (ROOT/'reports/V262-bellman-cascade.json').write_text(json.dumps(report,indent=2)+'\n')
for leaves in (63,255,511):
 ds=lgb.Dataset(x[:n][:,columns],label=gain);gate=lgb.train({'objective':'regression','learning_rate':1,'num_leaves':leaves,'max_depth':14,'min_data_in_leaf':150,'num_threads':1,'verbosity':-1,'deterministic':True,'force_col_wise':True,'boost_from_average':False,'seed':20261019},ds,num_boost_round=1);gate.save_model(str(out/f'regression-{leaves}.txt'));prediction=gate.predict(x[n:][:,columns],num_threads=1)
 for threshold in (.00005,.0001,.0002,.0005,.001,.002,.003,.005,.01,.02):
  selected=prediction>=threshold;p=np.where(selected,newv,oldv);path=f'regression-{leaves}-t{threshold:g}.npy';np.save(out/path,p)
  item={'kind':'regression','leaves':leaves,'threshold':threshold,'export_threshold':1/(1+math.exp(-threshold)),'score':score(yv,p),'physical_request_fraction':float(np.mean(selected)),'prediction':str((out/path).relative_to(ROOT))};report['candidates'].append(item);print(json.dumps(item),flush=True)
  (ROOT/'reports/V262-bellman-cascade.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V262-bellman-cascade.json').write_text(json.dumps(report,indent=2)+'\n')
