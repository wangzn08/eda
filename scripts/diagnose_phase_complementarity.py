"""Label-dependent diagnostic ceiling, never used as predictor."""
import numpy as np,json
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
_,y,_,_=load('validation');b=np.load(ROOT/'out/v117/route-data.npz')['validation_base'];pool=[];names=[]
for phase,glob in (('v127','near*.csv'),('v128','x*.csv'),('v130','x*.csv')):
 for f in sorted((ROOT/'out'/phase).glob(glob)):
  a=np.loadtxt(f,delimiter=',',skiprows=1,usecols=2,dtype=np.int64)
  if len(a)==len(y):pool.append(a);names.append(str(f.relative_to(ROOT)))
a=np.array([b,*pool]);delta=np.abs(a-y);q=a[delta.argmin(axis=0),np.arange(len(y))];r={'scope':'Label-dependent oracle ceiling only, not implementable predictor','base_score':score(y,b),'oracle_score':score(y,q),'oracle_improved_rows':int((np.abs(q-y)<np.abs(b-y)).sum()),'candidates':names,'holdout_used':False};(ROOT/'reports/V130-phase-complementarity-ceiling.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='candidates'}))
