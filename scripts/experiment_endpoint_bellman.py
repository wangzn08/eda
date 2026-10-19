"""Actual directed moves at both endpoints; development-only fitting.

The beam and ideal suffix are approximate. Scores here are offline research
until the same features/model are evaluated through the standard native CLI.
"""
import argparse,json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from native_research_labels import load_labels
from experiment_v7_teacher import score

p=argparse.ArgumentParser();p.add_argument('--version',default='255');p.add_argument('--ablations',action='store_true');p.add_argument('--profile-kind',choices=('bellman','envelope'),default='bellman');args=p.parse_args()
out=ROOT/f'out/v{args.version}';out.mkdir(exist_ok=True);report_path=ROOT/f'reports/V{args.version}-endpoint-bellman.json'
z=load_labels();y,yv=z['y'].astype(float),z['yv'].astype(float);n,nv=len(y),len(yv)
x=np.memmap(ROOT/'out/v243/all.features.f32',mode='r',dtype='<f4',shape=(n+nv,137))
raw=np.fromfile(out/'endpoint.features.bin',dtype=np.dtype([('base','<i4'),('profile','<f4',(16,))]))
assert len(raw)==n+nv
base=np.fromfile(ROOT/'out/v243/all.base.i32',dtype='<i4');assert np.array_equal(raw['base'],base)
b,bv=base[:n].astype(float),base[n:].astype(float)
extra=raw['profile'];names=json.loads((ROOT/'out/v216/features.json').read_text())
profile_names=['pair_base','beam_base','source1','target1','source2','target2','paired11','paired21','paired12','paired22','source_margin','target_margin','source1_entry','target1_entry','source2_entry','target2_entry']
if args.profile_kind=='envelope':profile_names=[f'{kind}_depth{depth}_scaled12' for kind in ('sum','maximum','source','target') for depth in (1,2,4)]+['second_margin','evaluated_sources','source_count','terminal_count']
names+=['bellman_'+s for s in profile_names];(out/'features.json').write_text(json.dumps(names,indent=2)+'\n')
all_features=np.column_stack([x,extra]).astype(np.float32);np.save(out/'features.npy',all_features)
report={'state':'running','holdout_used':False,'development_rows':n,'validation_rows':nv,'baseline_parity':True,'features':len(names),'profile_kind':args.profile_kind,'fit_scope':'development only; validation selection; approximate physical features, no shortest path guarantee','candidates':[],'references':['https://doi.org/10.1090/qam/102435']}
def record(item,p):
 item['score']=score(yv,p);item['exact_fraction']=float(np.mean(p==yv));report['candidates'].append(item)
 report_path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(item),flush=True)
for k in (range(2,10) if args.profile_kind=='bellman' else []):
 p=np.rint(np.maximum(0,bv+extra[n:,k]));record({'name':'raw-'+profile_names[k],'deployable':False},p)
params={'objective':'regression_l1','learning_rate':.2,'max_depth':24,'min_data_in_leaf':25,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019}
configs=[('global',list(range(16))),('wall-experts',list(range(16)))]
if args.ablations:configs += [('source1',[0,1,2,10,12]),('target1',[0,1,3,11,13]),('source2',[0,1,2,4,10,12,14]),('both1',[0,1,2,3,10,11,12,13])]
for kind,enabled in configs:
 start=time.monotonic();ids=(x[:n,54]>0) if kind=='wall-experts' else np.zeros(n,bool);idsv=(x[n:,54]>0) if kind=='wall-experts' else np.zeros(nv,bool)
 models=[]
 for d in range(2 if kind=='wall-experts' else 1):
  m=ids==bool(d);ds=lgb.Dataset(all_features[:n][m],label=(y-b)[m],weight=1000/np.maximum(y[m],1));model=lgb.train({**params,'num_leaves':511,'feature_contri':[1]*137+[int(i in enabled) for i in range(16)]},ds,num_boost_round=64);model.save_model(str(out/f'{kind}-{d}.txt'));models.append(model)
 for trees in (8,16,32,64):
  correction=np.zeros(nv)
  for d,model in enumerate(models):
   m=idsv==bool(d);correction[m]=model.predict(all_features[n:][m],num_iteration=trees,num_threads=1)
  p=np.rint(np.maximum(0,bv+correction));path=f'{kind}-{trees}.npy';np.save(out/path,p)
  record({'name':kind,'trees_per_request':trees,'total_trees':trees*len(models),'prediction':str((out/path).relative_to(ROOT)),'elapsed_seconds':time.monotonic()-start},p)
report['state']='complete';report['best']=max(report['candidates'],key=lambda v:v['score']);report_path.write_text(json.dumps(report,indent=2)+'\n');print('best',json.dumps(report['best']),flush=True)
