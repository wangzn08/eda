"""Measure accuracy/search cost tradeoff without asserting minimum-score guarantee."""
import csv,json,re,subprocess
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score
with (ROOT/'out/evaluation/v57-pilot.golden.csv').open() as f:g=list(csv.DictReader(f))
y=np.array([int(r['delay']) for r in g],dtype=float);items=[]
for error in (.00024,.0005,.001,.002,.005,.01):
    tag=str(error).replace('.','p');out=ROOT/f'out/evaluation/v75-{tag}.csv';cert=ROOT/f'out/evaluation/v75-{tag}.bounds.csv'
    cmd=['/usr/bin/time','-l','build/phase_estimate','-in','out/evaluation/v72-pilot.request.csv','-out',str(out),'--phase-bounds','models/phase-bounds-safe.bin','--cycle-oracle','out/phase-precision-v40/long-tail.bin','--no-cache','--relative-error',str(error),'--certificate',str(cert)]
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);(ROOT/f'out/v75-{tag}.log').write_text(r.stderr)
    with out.open() as f:rows=list(csv.DictReader(f))
    assert all((a['From'],a['To'])==(b['From'],b['To']) for a,b in zip(g,rows)) and len(rows)==len(g)
    p=np.array([int(a['delay']) for a in rows],dtype=float)
    with cert.open() as f:c=list(csv.DictReader(f))
    lo=np.array([int(a['lower']) for a in c],dtype=float);hi=np.array([int(a['upper']) for a in c],dtype=float)
    cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1])
    item={'relative_error_limit':error,'validation_pilot_score':score(y,p),'max_relative_error':float(np.max(np.abs(p-y)/np.maximum(y,1))),
          'invalid_intervals':int(np.sum((lo>y)|(hi<y))),'prediction_outside_interval':int(np.sum((p<lo)|(p>hi))),
          'settled':sum(int(a['settled']) for a in c),'query_cpu_seconds':cpu-init,'cpu_seconds':cpu}
    items.append(item);print(item,flush=True)
report={'rows':len(y),'holdout_used':False,'candidates':items,'scope':'Fixed validation pilot, one run per error limit. Looser bound does not guarantee99.9 score; no billion runtime extrapolation or final acceptance.'}
(ROOT/'reports/V75-precision-budget.json').write_text(json.dumps(report,indent=2)+'\n')
