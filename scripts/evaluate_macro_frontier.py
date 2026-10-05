"""Evaluate finite-frontier routing, approximate search with feasible outputs."""
import csv,json,re,subprocess
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score
with (ROOT/'out/evaluation/v57-pilot.golden.csv').open() as f:y=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=float)
items=[]
for beam,budget in ((0,128),(2,16),(4,16),(8,16),(4,64),(8,64),(16,64)):
    name=f'v69-beam{beam}-b{budget}';output=ROOT/f'out/evaluation/{name}.csv'
    cmd=['build/macro_oracle_apply','out/evaluation/v67-no-incumbent.csv',str(output),'out/phase-precision-v40/long-tail.bin',str(budget),'--gap-heuristic','--repeat-jumps','--priority-weight','1.05','--short-connectors','16','--cycle-initial-upper','--phase-bounds','out/architecture-benchmark/phase-bounds-long.bin','--frontier-limit',str(beam)]
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);(ROOT/f'out/{name}.log').write_text(r.stderr)
    with output.open() as f:p=np.array([int(row['delay']) for row in csv.DictReader(f)],dtype=float)
    m=p<1e8
    items.append({'frontier_limit':beam,'expansion_budget':budget,'covered':int(m.sum()),'exact_matches':int(np.sum(m&(p==y))),
                  'valid_under_golden':int(np.sum(m&(p<y))),'score_with_missing_zero':score(y,np.where(m,p,0)),
                  'query_cpu_seconds':float(re.search('cpu=([0-9.]+)',r.stderr)[1])})
report={'rows':len(y),'holdout_used':False,'external_initial_upper_used':False,'candidates':items,
        'scope':'Pilot single runs; internal initial-upper cost included, initialization excluded. Dropped frontier states invalidate search completeness/accuracy certificates; retained output paths remain feasible.'}
(ROOT/'reports/V69-frontier-selection.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
