"""Evaluate full inter-input connectivity pilot, validation only."""
import csv,json,re
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score
with (ROOT/'out/evaluation/v57-pilot.golden.csv').open() as f:y=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
report={'holdout_used':False,'rows':len(y),'scope':'All160 net-arrival ports and actual Arc/Net transitions; preexisting feasible initial bounds, bounded weighted search, no accuracy certificate. Pilot only.','candidates':[]}
for budget in (32,128):
    with (ROOT/f'out/evaluation/v65-all{budget}.csv').open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
    valid=p<1e8;log=(ROOT/f'out/v65-all{budget}.log').read_text()
    report['candidates'].append({'budget':budget,'covered':int(valid.sum()),'exact_matches':int(np.sum(valid&(p==y))),
                                'valid_under_golden':int(np.sum(valid&(p<y))),
                                'score_with_missing_zero':score(y,np.where(valid,p,0)),
                                'score_on_covered_only':score(y[valid],p[valid]),
                                'query_cpu_seconds':float(re.search('cpu=([0-9.]+)',log)[1]),'process_log':log.strip()})
(ROOT/'reports/V65-all-net-macro.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
