"""Development-only additive hashed phase corrections on frozen V59 model."""
import csv,json,time,sys
import numpy as np
from catboost import CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features
from experiment_v7_teacher import score
median='--median' in sys.argv
start=time.monotonic();folder=ROOT/('out/v70-median' if median else 'out/v70');folder.mkdir(exist_ok=True)
def delays(name):
    with (ROOT/'out/evaluation'/name).open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
x,y,_,_=load('development');v,yv,_,_=load('validation')
b=delays('development.v47-directional.csv');bv=delays('validation.v55-core.csv')
m=CatBoostRegressor();m.load_model(str(ROOT/'out/v59/correction.json'),format='json')
a=features(x,b);av=features(v,bv);a[:,27]=x[:,1]%100;a[:,28]=x[:,3]%100;av[:,27]=v[:,1]%100;av[:,28]=v[:,3]%100
p=np.rint(np.maximum(0,b+100*m.predict(a,ntree_end=256,thread_count=2)))
pv=np.rint(np.maximum(0,bv+100*m.predict(av,ntree_end=256,thread_count=2)))
def indices(z,bits):
    sp=z[:,10].astype(np.uint64);tp=z[:,11].astype(np.uint64);dx=(z[:,2]-z[:,0]).astype(np.int64);dy=(z[:,3]-z[:,1]).astype(np.int64)
    distance=(np.abs(dx)+np.abs(dy))//40;cross=((np.minimum(z[:,0],z[:,2])<76)&(np.maximum(z[:,0],z[:,2])>89)).astype(int)
    fields=[(sp,tp,dx%10,dy%12),(sp,tp,distance,np.sign(dx)+1,np.sign(dy)+1),
            (sp%8,tp%8,z[:,1]%100,z[:,3]%100,cross),
            (sp,tp,z[:,1]%12,z[:,3]%12),(sp//8,tp//8,dx%10,dy%12,distance)]
    result=[]
    for group in fields:
        h=np.full(len(z),1469598103934665603,dtype=np.uint64)
        for column in group:h=(h^np.asarray(column,dtype=np.uint64))*np.uint64(1099511628211)
        h^=h>>np.uint64(32);result.append((h&np.uint64((1<<bits)-1)).astype(np.int64))
    return result
report={'fit_split':'development','holdout_used':False,'baseline_score':score(yv,pv),'candidates':[]}
for bits in (14,16):
    ix=indices(x,bits);iv=indices(v,bits);size=1<<bits;tables=np.zeros((5,size),dtype=np.float32);f=p.copy();fv=pv.copy();w=1000/np.maximum(y,1)
    for epoch in range(4):
        for k in range(5):
            old=tables[k].astype(float);f-=old[ix[k]];fv-=old[iv[k]]
            residual=np.clip(y-f,-100,100)
            numerator=np.bincount(ix[k],weights=w*residual,minlength=size)
            denominator=np.bincount(ix[k],weights=w,minlength=size)
            if median:
                keys=np.concatenate((ix[k],np.arange(size)));values=np.concatenate((residual,np.zeros(size)));weights=np.concatenate((w,np.full(size,20.)))
                order=np.lexsort((values,keys));keys=keys[order];values=values[order];weights=weights[order]
                unique,starts=np.unique(keys,return_index=True);ends=np.r_[starts[1:],len(keys)]
                cumulative=np.cumsum(weights);before=np.where(starts>0,cumulative[np.maximum(starts-1,0)],0.)
                threshold=before+.5*(cumulative[ends-1]-before)
                positions=np.searchsorted(cumulative,threshold,side='left')
                updated=np.zeros(size);updated[unique]=.5*values[positions]
            else:updated=.5*numerator/(denominator+20)
            tables[k]=updated.astype(np.float32);f+=tables[k][ix[k]];fv+=tables[k][iv[k]]
        pred=np.rint(np.maximum(0,fv));name=f'hash{bits}-epoch{epoch+1}';np.save(folder/f'{name}.npy',pred);tables.tofile(folder/f'{name}.bin')
        item={'bits':bits,'epochs':epoch+1,'table_bytes':tables.nbytes,'validation_score':score(yv,pred)};report['candidates'].append(item);print(item,flush=True)
report['elapsed_seconds']=time.monotonic()-start;report['scope']='Additive hashed residuals keyed by port/period/distance/obstacle phase, regularized development fitting. Validation selection optimistic; no C++ throughput evidence yet.'
(ROOT/('reports/V70-hashed-phase-median.json' if median else 'reports/V70-hashed-phase-correction.json')).write_text(json.dumps(report,indent=2)+'\n')
