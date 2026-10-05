"""Evaluate architecture-only contracted two-net connectors, validation pilot."""
import csv,json,re,subprocess
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score
with (ROOT/'out/evaluation/v57-pilot.golden.csv').open() as f:y=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
items=[]
for limit,budget in ((0,32),(16,32),(64,32),(16,128),(64,128),(256,128)):
    name=f'v66-c{limit}-b{budget}';output=ROOT/f'out/evaluation/{name}.csv'
    command=['build/macro_oracle_apply','out/evaluation/v57-pilot.bound.csv',str(output),'out/phase-precision-v40/long-tail.bin',str(budget),'--gap-heuristic','--repeat-jumps','--priority-weight','1.05','--phase-bounds','models/phase-bounds-safe.bin','--short-connectors',str(limit)]
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=True);(ROOT/f'out/{name}.log').write_text(result.stderr)
    with output.open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
    valid=p<1e8
    items.append({'connectors_per_port':limit,'budget':budget,'covered':int(valid.sum()),'exact_matches':int(np.sum(valid&(p==y))),
                  'valid_under_golden':int(np.sum(valid&(p<y))),'score_with_missing_zero':score(y,np.where(valid,p,0)),
                  'query_cpu_seconds':float(re.search('cpu=([0-9.]+)',result.stderr)[1]),'log':result.stderr.strip()})
report={'holdout_used':False,'rows':len(y),'candidates':items,
        'scope':'Two actual Arc/Net moves contracted through short-wire input; architecture-only rank selection, initial oracle upper bound construction excluded, single pilot runs; not full throughput acceptance.'}
(ROOT/'reports/V66-short-connectors.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
