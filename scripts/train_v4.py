"""Train a compact LightGBM residual over frozen V3 using development labels."""
import json
import platform
import time

import lightgbm as lgb
import numpy as np

from architecture import ROOT
from v4_features import NAMES


def score(truth,pred):
    error=np.abs(pred-truth)/truth
    return float(np.mean(100*(1-np.tanh(4*error)),dtype=np.float64))


def main():
    start=time.monotonic()
    data=ROOT/'out/evaluation'
    train=np.load(data/'development.v4-features.npz')
    valid=np.load(data/'validation.v4-features.npz')
    x=train['x'];truth=train['truth'];base=train['baseline']
    good=(truth>0)&(base>0)
    label=(truth[good]-base[good])/base[good]
    x=x[good]
    xval=valid['x']; yval=valid['truth']; bval=valid['baseline']
    dataset=lgb.Dataset(x,label=label,feature_name=list(NAMES),free_raw_data=False)
    configs=[
        {'name':'l1-15','objective':'regression_l1','num_leaves':15,'max_depth':5},
        {'name':'huber-15','objective':'huber','alpha':0.85,'num_leaves':15,'max_depth':5},
        {'name':'l1-31','objective':'regression_l1','num_leaves':31,'max_depth':6},
    ]
    results=[]
    output=ROOT/'out/v4';output.mkdir(parents=True,exist_ok=True)
    for config in configs:
        name=config['name']
        params={'objective':config['objective'],'verbosity':-1,'learning_rate':0.08,
                'num_leaves':config['num_leaves'],'max_depth':config['max_depth'],
                'min_data_in_leaf':100,'feature_fraction':0.9,'bagging_fraction':0.9,
                'bagging_freq':1,'seed':20261004,'num_threads':2,
                'force_col_wise':True,'deterministic':True}
        if 'alpha' in config:params['alpha']=config['alpha']
        model=lgb.train(params,dataset,num_boost_round=96)
        model.save_model(str(output/f'{name}.txt'))
        for trees in (8,16,24,32,48,64,96):
            correction=model.predict(xval,num_iteration=trees,num_threads=2)
            for blend in (0.5,1.0):
                predicted=np.rint(np.maximum(0,bval*(1+blend*correction)))
                results.append({'model':name,'trees':trees,'blend':blend,
                                'score':score(yval,predicted),
                                'model_bytes':(output/f'{name}.txt').stat().st_size})
        print(name,max((r for r in results if r['model']==name),key=lambda r:r['score']),flush=True)
    best=max(results,key=lambda r:r['score'])
    report={'baseline_score':score(yval,bval),'best':best,'candidates':results,
            'features':list(NAMES),'development_rows':int(good.sum()),
            'validation_rows':len(yval),'lightgbm_version':lgb.__version__,
            'numpy_version':np.__version__,'machine':platform.platform(),
            'elapsed_seconds':time.monotonic()-start,'holdout_used':False}
    (ROOT/'reports/V4-tree-research.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'baseline':report['baseline_score'],'best':best,
                      'elapsed_seconds':report['elapsed_seconds']},indent=2),flush=True)


if __name__=='__main__':main()
