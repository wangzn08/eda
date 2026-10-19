"""Allocate endpoint computation using cross-fitted gain per estimated work.

Work is an architecture-derived proxy, not a measured per-request CPU timer.
Only a standard native benchmark can establish the candidate's actual cost.
"""
import csv,json,math
import numpy as np,lightgbm as lgb
from architecture import ROOT
from native_research_labels import load_labels
from experiment_v7_teacher import score
out=ROOT/'out/v269';out.mkdir(exist_ok=True)
z=load_labels();y,yv=z['y'].astype(float),z['yv'].astype(float);n=len(y);x=np.load(ROOT/'out/v255/features.npy',mmap_mode='r');oof=np.load(ROOT/'out/v262/oof.npz')
gain=np.tanh(4*abs(oof['old']-y)/np.maximum(y,1))-np.tanh(4*abs(oof['new']-y)/np.maximum(y,1));counts=np.fromfile(ROOT/'out/v259/endpoint.features.bin',dtype=[('b','<i4'),('f','<f4',(16,))])['f'];work=1+counts[:,14]*counts[:,15]/128
columns=list(range(69))+list(range(125,137));(out/'gate-features.json').write_text(json.dumps(columns)+'\n')
old=np.array([int(r['delay']) for r in csv.DictReader((ROOT/'out/v254/score-profile/validation.csv').open())]);new={'rich32':np.load(ROOT/'out/v255/wall-experts-32.npy'),'seeded32':np.load(ROOT/'out/v266/wall-experts-32.npy'),'seeded16':np.load(ROOT/'out/v266/wall-experts-16.npy')}
report={'state':'running','fit_scope':'two-fold development cross-fitted loss gain divided by architecture-only call-count proxy; validation comparison only','holdout_used':False,'work_proxy':'1+source_count*terminal_count/128, not actual CPU','candidates':[]}
gate=lgb.train({'objective':'regression','learning_rate':1,'num_leaves':511,'max_depth':14,'min_data_in_leaf':150,'num_threads':1,'verbosity':-1,'deterministic':True,'force_col_wise':True,'boost_from_average':False,'seed':20261019},lgb.Dataset(x[:n][:,columns],label=gain/work[:n],weight=work[:n]),num_boost_round=1);gate.save_model(str(out/'work-gain.txt'))
gates={'work-gain':gate,'raw-gain':lgb.Booster(model_file=str(ROOT/'out/v262/regression-511.txt'))}
for name,gate in gates.items():
 value=gate.predict(x[n:][:,columns],num_threads=1)
 for threshold in (.0003,.0005,.00075,.001,.0015,.002,.0025,.003,.004,.005,.01):
  selected=value>=threshold
  for expert,prediction in new.items():
   p=np.where(selected,prediction,old);path=f'{name}-{expert}-t{threshold:g}.npy';np.save(out/path,p)
   item={'gate':name,'expert':expert,'threshold':threshold,'export_threshold':1/(1+math.exp(-threshold)),'score':score(yv,p),'physical_request_fraction':float(np.mean(selected)),'selected_work_proxy_mean':float(np.mean(work[n:]*selected)),'prediction':str((out/path).relative_to(ROOT))};report['candidates'].append(item);print(json.dumps(item),flush=True)
   (ROOT/'reports/V269-work-budget.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V269-work-budget.json').write_text(json.dumps(report,indent=2)+'\n')
