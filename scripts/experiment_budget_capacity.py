"""Use the measured fixed-layout speed margin for stronger cheap-feature models."""
import json,time
import lightgbm as lgb,numpy as np
from architecture import ROOT
from native_research_labels import load_labels
out=ROOT/'out/v307';out.mkdir(exist_ok=True);f=np.load(ROOT/'out/v288/features.npy');b=np.load(ROOT/'out/v276/base.npy');z=load_labels();y,yv=z['y'],z['yv'];n=len(y)
(out/'port-metadata.json').write_bytes((ROOT/'out/v288/port-metadata.json').read_bytes())
report={'state':'running','fit_scope':'development only','holdout_used':False,'features':56,'candidates':[]}
for name,leaves,trees,rate in [('sixteen511',511,16,.2),('thirtytwo511',511,32,.12),('thirtytwo1023',1023,32,.12),('sixtyfour511',511,64,.08),('sixtyfour1023',1023,64,.08)]:
 start=time.monotonic();m=lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':24,'min_data_in_leaf':30,'learning_rate':rate,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019},lgb.Dataset(f[:n],label=y-b[:n],weight=1000/np.maximum(y,1)),num_boost_round=trees);m.save_model(str(out/f'{name}.txt'));pred=np.rint(np.maximum(0,b[n:]+m.predict(f[n:],num_threads=1)));np.save(out/f'{name}.npy',pred)
 item={'name':name,'leaves':leaves,'trees':trees,'score':float(100*np.mean(1-np.tanh(4*abs(pred-yv)/np.maximum(yv,1)))),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V307-capacity.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V307-capacity.json').write_text(json.dumps(report,indent=2)+'\n')
