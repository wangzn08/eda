"""Compare a small predefined set of model combinations; validation selection only."""
import csv,json
import numpy as np
from architecture import ROOT
from interval_architecture_data import load_interval
from experiment_v7_teacher import score

def prediction(report,stem,kind):
    best=json.loads((ROOT/'reports'/report).read_text())['best']
    if kind=='graph':name=f"validation-{int(best['graph_embedding'])}-{best['epoch']}-{best['v19_weight']}.npy"
    elif kind=='interval':name=f"validation-{best['routes']}-{best['epoch']}-{best['v19_weight']}.npy"
    else:name=f"validation-{best['epoch']}-{best['v19_weight']}.npy"
    return np.load(ROOT/'out'/stem/name),best

def main():
    x,y,b,u,lower=load_interval('validation');root=ROOT/'out/evaluation';models={};config={}
    for key,report,stem,kind in [('phase','V27-minplus-neural.json','v27','plain'),('minplus','V24-minplus-neural.json','v24','plain'),
      ('interval','V26-interval-minplus.json','v26','interval'),('mlp','V21-neural-architecture.json','v21','graph'),('transit','V28-minplus-neural.json','v28','plain')]:
        models[key],config[key]=prediction(report,stem,kind)
    with (root/'validation.v30-bound.csv').open() as f:rows=list(csv.DictReader(f))
    with (root/'validation.golden.csv').open() as f:gold=list(csv.DictReader(f))
    assert len(rows)==len(gold) and all((a['From'],a['To'])==(b['From'],b['To']) for a,b in zip(rows,gold))
    upper=np.array([int(r['delay']) for r in rows]);assert np.all(upper>=y)
    folder=ROOT/'out/architecture-benchmark';results=[]
    for key,p in models.items():
        capped=np.clip(p,lower,upper);name=f'{key}-macro';np.save(folder/f'{name}.npy',capped)
        results.append({'name':name,'validation_score':score(y,capped),'weights':{key:1}})
    for key in ('minplus','interval','mlp','transit'):
        for weight in (.25,.5,.75):
            p=np.clip(np.rint((1-weight)*models['phase']+weight*models[key]),lower,upper);name=f'phase-{key}-{weight}'
            np.save(folder/f'{name}.npy',p);results.append({'name':name,'validation_score':score(y,p),'weights':{'phase':1-weight,key:weight}})
    report={'fit_split':'development','selection_split':'validation','holdout_used':False,'macro_budget':65536,
      'lower_bound_violations':0,'upper_bound_violations':0,'models':config,'candidates':results,'best':max(results,key=lambda z:z['validation_score'])}
    (ROOT/'reports/V30-architecture-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in sorted(results,key=lambda z:z['validation_score'],reverse=True):print(json.dumps(r),flush=True)

if __name__=='__main__':main()
