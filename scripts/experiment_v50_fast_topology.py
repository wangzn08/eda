"""Compact oblivious residual trees above the architecture PDB; development labels only."""
import csv,json,time
import numpy as np
from catboost import CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score

def features(x,lower):
    # All columns available without route upper banks or prior learned predictors.
    ids=list(range(9))+list(range(10,22))
    z=x[:,ids].astype(np.float32)
    return np.column_stack((z,lower,lower-12.5*x[:,6]-125/12*x[:,7]-x[:,20]-x[:,21],x[:,4]%10,x[:,5]%12,x[:,4]%4,x[:,5]%4,x[:,10]%8,x[:,11]%8,x[:,31:73])).astype(np.float32)

def lower(split):
    with (ROOT/f'out/evaluation/{split}.v41-lower.csv').open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float32)

def main():
    start=time.monotonic();folder=ROOT/'out/v50';folder.mkdir(exist_ok=True)
    x,y,_,_=load('development');xv,yv,_,_=load('validation');lo=lower('development');lv=lower('validation');a=features(x,lo);av=features(xv,lv);m=y>0
    assert len(lo)==len(y);assert np.all(lo<=y)
    report={'fit_split':'development','holdout_used':False,'architecture':'PDB anchored oblivious residual trees with endpoint graph and long-wire access features; no route search or upper-bank runtime','candidates':[]}
    for depth in (10,):
        model=CatBoostRegressor(iterations=1024,depth=depth,learning_rate=.08,loss_function='MAE',thread_count=2,random_seed=20261005,l2_leaf_reg=5,verbose=128,allow_writing_files=False)
        model.fit(a[m],(y[m]-lo[m])/100,sample_weight=1/np.maximum(y[m],1))
        model.save_model(str(folder/f'residual-{depth}.json'),format='json')
        for trees in (64,128,256,512,1024):
            pred=np.rint(lv+np.maximum(0,100*model.predict(av,ntree_end=trees,thread_count=2)))
            item={'depth':depth,'trees':trees,'score':score(yv,pred)};report['candidates'].append(item);np.save(folder/f'validation-{depth}-{trees}.npy',pred);print(json.dumps(item),flush=True)
        report['elapsed']=time.monotonic()-start;(ROOT/'reports/V50-fast-topology-residual.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
