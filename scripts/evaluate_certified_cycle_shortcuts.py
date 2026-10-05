"""Audit certified shortcut search on aligned validation pilot."""
import csv,json,re
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score
with (ROOT/'out/evaluation/v57-pilot.golden.csv').open() as f:g=list(csv.DictReader(f))
with (ROOT/'out/evaluation/v74-shortcuts.csv').open() as f:r=list(csv.DictReader(f))
assert len(g)==len(r)==1001
assert all((a['From'],a['To'])==(b['From'],b['To']) for a,b in zip(g,r))
y=np.array([int(a['delay']) for a in g],dtype=float);p=np.array([int(a['delay']) for a in r],dtype=float)
def certificates(name):
    with (ROOT/'out/evaluation'/name).open() as f:return list(csv.DictReader(f))
c=certificates('v74-shortcuts.bounds.csv');b=certificates('v72-dictionary.bounds.csv')
lo=np.array([int(a['lower']) for a in c],dtype=float);hi=np.array([int(a['upper']) for a in c],dtype=float)
log=(ROOT/'out/v74-shortcuts.log').read_text();cpu=float(re.search('cpu_seconds=([0-9.]+)',log)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',log)[1])
report={'rows':len(y),'holdout_used':False,'score':score(y,p),'max_relative_error':float(np.max(np.abs(p-y)/np.maximum(y,1))),
        'invalid_intervals':int(np.sum((lo>y)|(hi<y))),'prediction_outside_interval':int(np.sum((p<lo)|(p>hi))),
        'baseline_settled':sum(int(a['settled']) for a in b),'shortcut_settled':sum(int(a['settled']) for a in c),
        'baseline_relaxations':sum(int(a['relaxations']) for a in b),'shortcut_relaxations':sum(int(a['relaxations']) for a in c),
        'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':cpu-init,
        'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',log)[1]),
        'scope':'Actual cycle shortcut edges added without removing original graph edges; validation pilot only, one timing run, no full acceptance.',
        'decision':'Do not enable by default: negligible expansion reduction and more relaxations.'}
(ROOT/'reports/V74-certified-cycle-shortcuts.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
