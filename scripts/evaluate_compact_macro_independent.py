"""Evaluate compact macro routes without an externally constructed incumbent."""
import csv,json,re,subprocess
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score
with (ROOT/'out/evaluation/v57-pilot.golden.csv').open() as f:gold=list(csv.DictReader(f))
y=np.array([int(r['delay']) for r in gold],dtype=np.float64)
# Request identities are taken from request/bound input; delay is always infinity.
with (ROOT/'out/evaluation/v57-pilot.bound.csv').open() as src,(ROOT/'out/evaluation/v67-no-incumbent.csv').open('w') as dst:
    w=csv.writer(dst);w.writerow(['From','To','delay'])
    for r in csv.DictReader(src):w.writerow([r['From'],r['To'],100000000])
items=[]
for phase,budget,initial in ((False,32,False),(False,128,False),(False,512,False),(True,128,False),(False,128,True),(True,128,True)):
    name=f'v67-phase{int(phase)}-b{budget}-i{int(initial)}';out=ROOT/f'out/evaluation/{name}.csv'
    cmd=['/usr/bin/time','-l','build/macro_oracle_apply','out/evaluation/v67-no-incumbent.csv',str(out),'out/phase-precision-v40/long-tail.bin',str(budget),'--gap-heuristic','--repeat-jumps','--priority-weight','1.05','--short-connectors','16']
    if initial:cmd.append('--cycle-initial-upper')
    if phase:cmd+=['--phase-bounds','models/phase-bounds-safe.bin']
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);(ROOT/f'out/{name}.log').write_text(r.stderr)
    with out.open() as f:p=np.array([int(row['delay']) for row in csv.DictReader(f)],dtype=np.float64)
    valid=p<1e8
    items.append({'internal_cycle_initial_upper':initial,'phase_bound':phase,'budget':budget,'covered':int(valid.sum()),'exact_matches':int(np.sum(valid&(p==y))),
                  'valid_under_golden':int(np.sum(valid&(p<y))),'score_with_missing_zero':score(y,np.where(valid,p,0)),
                  'query_cpu_seconds':float(re.search(r'rows=1001.*cpu=([0-9.]+)',r.stderr)[1]),
                  'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1])})
report={'holdout_used':False,'external_initial_upper_used':False,'rows':len(y),'candidates':items,
        'scope':'Every query starts with infinity; score uses golden only after inference. Query CPU excludes architecture/tail initialization; pilot only, no final throughput proof.'}
(ROOT/'reports/V67-independent-compact-macro.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
