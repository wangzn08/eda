"""Add static architecture port semantics to the tiny 600 s residual learner."""
import json,time,re,argparse,csv
import numpy as np,lightgbm as lgb
from architecture import ROOT,Architecture
from native_research_labels import load_labels
p=argparse.ArgumentParser();p.add_argument('--version',default='288');p.add_argument('--base-predictions');args=p.parse_args();out=ROOT/f'out/v{args.version}';out.mkdir(exist_ok=True);a=Architecture();types={};meta=np.zeros((len(a.ports),8),np.int32);meta[:,1:4]=-1
for i,p in enumerate(a.ports):
 m=re.fullmatch(r'(.*)\[(\d+)\]',p['Name']);family=m[1] if m else p['Name'];meta[i,0]=types.setdefault(family,len(types));meta[i,1]=int(m[2]) if m else -1
for i,net in enumerate(a.nets):
 source,target=a.port_ids[net['from']],a.port_ids[net['to']]
 for port in (source,target):meta[port,2]=i%20;meta[port,3]=i//20
 meta[source,4:6]=[net['delta x'],net['delta y']];meta[target,6:8]=[net['delta x'],net['delta y']]
(out/'port-metadata.json').write_text(json.dumps(meta.tolist())+'\n')
x=np.load(ROOT/'out/v276/features.npy');b=np.load(ROOT/'out/v276/base.npy');
if args.base_predictions:
 with (ROOT/args.base_predictions).open() as f:b=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
 assert len(b)==len(x);x[:,31]+=12*(b-x[:,0]);x[:,0]=b
sp=x[:,5].astype(int);tp=x[:,6].astype(int)
adx=x[:,7]-meta[sp,4]-meta[tp,6];ady=x[:,8]-meta[sp,5]-meta[tp,7]
f=np.column_stack([x,meta[sp],meta[tp],adx,ady,abs(adx),abs(ady),(adx%10+10)%10,(ady%12+12)%12]).astype(np.float32);assert f.shape[1]==56
np.save(out/'features.npy',f);labels=load_labels();y,yv=labels['y'],labels['yv'];n=len(y)
report={'state':'running','fit_scope':'development labels only; static architecture port semantics','holdout_used':False,'features':56,'candidates':[]}
for name,leaves,trees,rate in [('one511',511,1,1),('one2047',2047,1,1),('one8191',8191,1,1),('two1023',1023,2,.6),('four511',511,4,.4),('eight511',511,8,.3),('sixteen511',511,16,.2)]:
 start=time.monotonic();m=lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':24,'min_data_in_leaf':30,'learning_rate':rate,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019},lgb.Dataset(f[:n],label=y-b[:n],weight=1000/np.maximum(y,1)),num_boost_round=trees)
 m.save_model(str(out/f'{name}.txt'));pred=np.rint(np.maximum(0,b[n:]+m.predict(f[n:],num_threads=1)));np.save(out/f'{name}.npy',pred)
 item={'name':name,'leaves':leaves,'trees':trees,'score':float(100*np.mean(1-np.tanh(4*abs(pred-yv)/np.maximum(yv,1)))),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/f'reports/V{args.version}-port-residual.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/f'reports/V{args.version}-port-residual.json').write_text(json.dumps(report,indent=2)+'\n')
