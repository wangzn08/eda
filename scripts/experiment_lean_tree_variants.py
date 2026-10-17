"""Compare one/few trees with route response and endpoint interactions."""
import argparse,json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--version',required=True);args=p.parse_args()
source=ROOT/args.input;out=ROOT/'out'/args.version;out.mkdir(exist_ok=True)
f=np.load(source/'fit.npz');z=np.load(ROOT/'out/v125/fit-features.npz');names=json.loads((source/'features.json').read_text());extra_names=[]
def interactions(a):
    d={name:a[:,i] for i,name in enumerate(names)};new={}
    for depth in range(3):
        s=d[f'source_direction_phi_0_{depth}'];t=d[f'target_direction_phi_1_{depth}']
        new[f'endpoint_sum_{depth}']=s+t;new[f'endpoint_max_{depth}']=np.maximum(s,t);new[f'endpoint_min_{depth}']=np.minimum(s,t)
    new['endpoint_sum_growth']=new['endpoint_sum_2']-new['endpoint_sum_1']
    new['endpoint_max_growth']=new['endpoint_max_2']-new['endpoint_max_1']
    bank_dx=d['dx']-np.sign(d['dx'])*14*(d['kind']==2);bank_qx=np.where(abs(bank_dx)>29,(abs(bank_dx)-20)//10,0)
    intrinsic=d['nominal']-d['arc']-292*(d['kind']==2)-125*bank_qx-np.where(d['dy']>0,127,125)*d['qy']
    new['bank_dx']=bank_dx;new['bank_qx']=bank_qx;new['intrinsic_residual']=intrinsic
    new['intrinsic_vs_period8']=intrinsic-d['response_2']
    if 'response_8' in d:
        new['period4_to8_slope']=(d['response_2']-d['response_8'])/4
        new['intrinsic_vs_bridge']=intrinsic-(d['response_8']+(d['qy']-4)*new['period4_to8_slope'])
    for k in ['source','end']:
        new[k+'_vector_along_x']=d['core_incoming_0' if k=='source' else 'end_incoming_0']*np.sign(d['dx'])
        new[k+'_vector_along_y']=d['core_incoming_1' if k=='source' else 'end_incoming_1']*np.sign(d['dy'])
    return np.column_stack([a,*new.values()]).astype(np.float32),list(new)
a,extra_names=interactions(f['a']);av,extra_v=interactions(f['av']);assert extra_names==extra_v;all_names=names+extra_names
(out/'features.json').write_text(json.dumps(all_names,indent=2)+'\n');np.savez(out/'fit.npz',a=a,av=av,b=f['b'],bv=f['bv'])
def score(v):return float(100*np.mean(1-np.tanh(4*abs(v-z['yv'])/z['yv'])))
cats=[i for i,name in enumerate(all_names) if name in ['source_category','target_category','core_type','end_type','core_lane','end_lane']]
spec=[('deep24',32767,24,8,1,1,False),('deep32',32767,32,8,1,1,False),('wide32',65535,32,4,1,1,False),('two',8191,24,15,2,1,False),('four',4095,24,15,4,.7,False),('eight',2047,24,15,8,.5,False),('cat_one',32767,24,8,1,1,True),('cat_two',8191,24,15,2,1,True),('cat_eight',2047,24,15,8,.5,True)]
report={'state':'running','input':args.input,'fit_scope':'development golden residual only','holdout_used':False,'features':len(all_names),'new_features':extra_names,'base_score':score(f['bv']),'scope':'One/few-tree accuracy and model-size screen; native performance unproven','candidates':[]}
for name,leaves,depth,minimum,trees,rate,cat in spec:
    start=time.monotonic();ds=lgb.Dataset(a,label=z['y']-f['b'],weight=1000/np.maximum(z['y'],1),categorical_feature=cats if cat else [])
    model=lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':depth,'min_data_in_leaf':minimum,'learning_rate':rate,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261008,'min_data_per_group':10,'cat_smooth':5,'cat_l2':1},ds,num_boost_round=trees)
    path=out/f'{name}.txt';model.save_model(str(path));prediction=np.rint(np.maximum(0,f['bv']+model.predict(av,num_threads=1)));np.save(out/f'{name}.npy',prediction)
    item={'model':name,'score':score(prediction),'bytes':path.stat().st_size,'trees':trees,'num_leaves':leaves,'depth':depth,'minimum_leaf':minimum,'categorical':cat,'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports'/f'{args.version.upper()}-lean-tree-variants.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports'/f'{args.version.upper()}-lean-tree-variants.json').write_text(json.dumps(report,indent=2)+'\n')
