"""Lean selected-route model, development golden residual fitting only."""
import argparse,json,time
import numpy as np,lightgbm as lgb
from architecture import ROOT
from selected_curve_features import read_selection,selected_features
parser=argparse.ArgumentParser();parser.add_argument('--prefix',required=True);parser.add_argument('--version',required=True);args=parser.parse_args()
prefix=ROOT/args.prefix;out=ROOT/'out'/args.version;out.mkdir(exist_ok=True)
z=np.load(ROOT/'out/v125/fit-features.npz');n=len(z['y']);prediction=np.fromfile(str(prefix)+'.i32',dtype='<i4').astype(np.float32);assert len(prediction)==n+len(z['yv'])
records,response=read_selection(prefix);assert len(records)==len(prediction)
a,names=selected_features(z['a'],records[:n],response[:n],prediction[:n]);av,namesv=selected_features(z['av'],records[n:],response[n:],prediction[n:]);assert names==namesv
(out/'features.json').write_text(json.dumps(names,indent=2)+'\n')
np.savez(out/'fit.npz',a=a,av=av,b=prediction[:n],bv=prediction[n:])
def score(p):return float(100*np.mean(1-np.tanh(4*np.abs(p-z['yv'])/z['yv'])))
r={'state':'running','fit_scope':'development labels only, features from the current selected architecture route; no old predictor descriptors','holdout_used':False,'base_score':score(prediction[n:]),'feature_count':len(names),'scope':'Accuracy and model-size pilot; standard native speed/storage/RSS unproven','candidates':[]}
for name,leaves,trees,rate in [('tree1',8191,1,1),('tree8',1023,8,.3),('compact',127,64,.07),('large',511,256,.07)]:
    start=time.monotonic();ds=lgb.Dataset(a,label=z['y']-prediction[:n],weight=1000/np.maximum(z['y'],1))
    model_path=out/f'{name}.txt'
    reused=model_path.exists()
    model=lgb.Booster(model_file=str(model_path)) if reused else lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':24,'min_data_in_leaf':30,'learning_rate':rate,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261008},ds,num_boost_round=trees)
    model.save_model(str(out/f'{name}.txt'));p=np.rint(np.maximum(0,prediction[n:]+model.predict(av,num_threads=1)));np.save(out/f'{name}.npy',p)
    item={'model':name,'score':score(p),'elapsed_seconds':time.monotonic()-start,'features_used':int(sum(model.feature_importance()>0)),'reused_saved_model':reused};r['candidates'].append(item);print(json.dumps(item),flush=True)
    (ROOT/'reports'/f'{args.version.upper()}-selected-residual.json').write_text(json.dumps(r,indent=2)+'\n')
r['state']='complete';(ROOT/'reports'/f'{args.version.upper()}-selected-residual.json').write_text(json.dumps(r,indent=2)+'\n')
