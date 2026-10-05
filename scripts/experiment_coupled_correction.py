"""Development-fit signed residual model on coupled horizontal/vertical baseline."""
import csv,json,subprocess,time
import numpy as np
from catboost import CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features
from experiment_v7_teacher import score
folder=ROOT/'out/v82';folder.mkdir(exist_ok=True);start=time.monotonic()
def read(p):
    with p.open() as f:return np.array([int(a['delay']) for a in csv.DictReader(f)],dtype=np.float32)
basepath=ROOT/'out/evaluation/development.v82-coupled.csv'
if not basepath.exists():
    r=subprocess.run(['out/phase-coupled-v81/estimate','-in','out/evaluation/development.request.csv','-out',str(basepath),'--no-cache'],cwd=ROOT,capture_output=True,text=True,check=True);(folder/'development-base.log').write_text(r.stderr)
x,y,_,_=load('development');v,yv,_,_=load('validation');b=read(basepath);bv=read(ROOT/'out/evaluation/validation.v81-profile.csv')
a=features(x,b);av=features(v,bv);a[:,27]=x[:,1]%100;a[:,28]=x[:,3]%100;av[:,27]=v[:,1]%100;av[:,28]=v[:,3]%100
model=CatBoostRegressor(iterations=256,depth=10,learning_rate=.07,loss_function='MAE',thread_count=2,random_seed=20261010,l2_leaf_reg=5,verbose=64,allow_writing_files=False)
mask=y>0;model.fit(a[mask],(y[mask]-b[mask])/100,sample_weight=1/np.maximum(y[mask],1));source=folder/'correction.json';model.save_model(str(source),format='json')
items=[]
for trees in (64,128,256):
    p=np.rint(np.maximum(0,bv+100*model.predict(av,ntree_end=trees,thread_count=2)));np.save(folder/f'validation-{trees}.npy',p)
    subprocess.run([str(ROOT/'out/research-env/bin/python'),'scripts/export_fast_residual.py',str(source),str(folder/f'correction-{trees}.bin'),'--trees',str(trees),'--obstacle-phase'],cwd=ROOT,check=True)
    out=ROOT/f'out/evaluation/validation.v82-{trees}.csv'
    cmd=['/usr/bin/time','-l','build/core_template_estimate','--model','out/architecture-benchmark/core-template-xz6.bin','--vertical-transients','out/architecture-benchmark/vertical-transients-xz.bin','--horizontal-transients','out/architecture-benchmark/horizontal-transients.bin','--residual-model',str(folder/f'correction-{trees}.bin'),'--trees',str(trees),'-in','out/evaluation/validation.request.csv','-out',str(out),'--no-cache']
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);(folder/f'validation-{trees}.log').write_text(r.stderr)
    cpp=read(out);items.append({'trees':trees,'python_score':score(yv,p),'cpp_score':score(yv,cpp),'prediction_mismatches':int(np.sum(cpp!=p))});print(items[-1],flush=True)
report={'fit_split':'development','holdout_used':False,'baseline_score':score(yv,bv),'candidates':items,'elapsed_seconds':time.monotonic()-start,
        'scope':'New transient-baseline residual models; full validation and C++ parity, no standalone throughput or official acceptance yet.'}
(ROOT/'reports/V82-coupled-correction.json').write_text(json.dumps(report,indent=2)+'\n')
