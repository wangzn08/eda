import csv,json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
_,y,_,_=load('validation');rows=[]
for path in sorted((ROOT/'out/v140/validation').glob('*.csv')):
 with path.open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
 assert len(p)==len(y)==150053
 rows.append({'name':path.stem,'score':score(y,p),'exact_fraction':float(np.mean(p==y))})
r={'state':'complete','scope':'Full validation, research raw asset; no final timing/budget qualification','cases':rows,'holdout_used':False,'prediction_cache':False}
(ROOT/'reports/V140-physical-portals-validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
