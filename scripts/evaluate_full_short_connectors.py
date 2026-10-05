"""Full validation audit of contracted connector path candidates."""
import csv,json,re
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
_,y,_,_=load('validation')
def read(path):
    with path.open() as f:return np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
u=read(ROOT/'out/evaluation/validation.v66-connectors.csv');p=read(ROOT/'out/evaluation/validation.v59-profile.csv')
assert len(u)==len(p)==len(y)
valid=u<1e8;log=(ROOT/'out/v66-full.log').read_text()
r={'rows':len(y),'holdout_used':False,'covered':int(valid.sum()),'exact_matches':int(np.sum(valid&(u==y))),
   'valid_under_golden':int(np.sum(valid&(u<y))),'path_score_with_missing_zero':score(y,np.where(valid,u,0)),
   'v59_score':score(y,p),'v59_clipped_to_feasible_upper_score':score(y,np.where(valid,np.minimum(p,u),p)),
   'clipped_rows':int(np.sum(valid&(u<p))),
   'query_cpu_seconds':float(re.search(r'rows=150053.*cpu=([0-9.]+)',log)[1]),
   'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',log)[1]),
   'scope':'Complete validation, architecture witness upper candidates. CPU excludes initialization and initial upper construction; clipping score is offline analysis, no matching standalone hybrid runtime yet. No billion acceptance.'}
(ROOT/'reports/V66-full-connectors.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
