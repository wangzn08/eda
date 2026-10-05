"""Learn route-template interaction from alternative entry/exit representatives."""
import csv,json,subprocess,time,sys
import numpy as np
from catboost import CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features
from experiment_v7_teacher import score
control='--control' in sys.argv
folder=ROOT/('out/v71-control' if control else 'out/v71');folder.mkdir(exist_ok=True);start=time.monotonic()
def read(path):
    with path.open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float32)
x,y,_,_=load('development');v,yv,_,_=load('validation')
b=read(ROOT/'out/evaluation/development.v47-directional.csv');bv=read(ROOT/'out/evaluation/validation.v55-core.csv')
train=[];valid=[]
for sx,sy in ((1,0),(0,1),(1,1)):
    name=f'development.v71-shell-{sx}-{sy}';out=ROOT/f'out/evaluation/{name}.csv'
    if not out.exists():
        result=subprocess.run(['build/core_template_estimate','--model','out/architecture-benchmark/core-template-zlib.bin','--shell-x',str(sx),'--shell-y',str(sy),'-in','out/evaluation/development.request.csv','-out',str(out),'--no-cache'],cwd=ROOT,capture_output=True,text=True,check=True)
        (folder/f'shell-{sx}-{sy}.log').write_text(result.stderr)
    train.append(read(out)-b);valid.append(read(ROOT/f'out/evaluation/v61-shell-{sx}-{sy}.csv')-bv)
a=features(x,b);av=features(v,bv);a[:,27]=x[:,1]%100;a[:,28]=x[:,3]%100;av[:,27]=v[:,1]%100;av[:,28]=v[:,3]%100
# Signed differences reveal entry/exit transient sensitivity, no golden candidate selection.
if not control:a=np.column_stack((a,*train));av=np.column_stack((av,*valid))
model=CatBoostRegressor(iterations=256,depth=10,learning_rate=.07,loss_function='MAE',thread_count=2,random_seed=20261012,l2_leaf_reg=5,verbose=64,allow_writing_files=False)
mask=y>0;model.fit(a[mask],(y[mask]-b[mask])/100,sample_weight=1/np.maximum(y[mask],1));model.save_model(str(folder/'correction.json'),format='json')
items=[]
for n in (64,128,256):
    pred=np.rint(np.maximum(0,bv+100*model.predict(av,ntree_end=n,thread_count=2)));np.save(folder/f'validation-{n}.npy',pred)
    items.append({'trees':n,'validation_score':score(yv,pred)})
report={'fit_split':'development','holdout_used':False,'feature_count':a.shape[1],'candidates':items,'elapsed_seconds':time.monotonic()-start,
        'scope':'Alternative template signed differences as topology features; trained model only, no C++ parity or runtime proof yet. Alternative templates are approximate, not path certificates.'}
(ROOT/('reports/V71-shell-control-model.json' if control else 'reports/V71-shell-structure-model.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
