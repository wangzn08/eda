"""Measure full-request macro search before/after witnessed cycle doubling."""
import csv,json,re,subprocess,hashlib,sys
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score
with (ROOT/'out/evaluation/v57-pilot.golden.csv').open() as f:y=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
phase='--phase' in sys.argv
report={'phase_bound':phase,'holdout_used':False,'rows':len(y),'budget':32,'priority_weight':1.05,'variants':{}}
for mode in ('direct','doubling'):
    runs=[];output=ROOT/f'out/evaluation/v64-{mode}.csv'
    command=['/usr/bin/time','-l','build/macro_oracle_apply','out/evaluation/v57-pilot.bound.csv',str(output),'out/phase-precision-v40/long-tail.bin','32','--gap-heuristic','--repeat-jumps','--priority-weight','1.05']
    if phase:command.extend(['--phase-bounds','models/phase-bounds-safe.bin'])
    if mode=='doubling':command.append('--cycle-doubling')
    for i in range(5):
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=True)
        (ROOT/f'out/v64-{mode}-{"phase" if phase else "potential"}-{i}.log').write_text(result.stderr)
        runs.append({'query_cpu_seconds':float(re.search(r' cpu=([0-9.]+)',result.stderr)[1]),
                     'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',result.stderr)[1]),
                     'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
    with output.open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
    covered=p<1e8
    report['variants'][mode]={'runs':runs,'covered':int(covered.sum()),'score_with_missing_zero':score(y,np.where(covered,p,0)),
                             'valid_path_under_golden':int(np.sum(covered&(p<y))),
                             'median_query_cpu_seconds':float(np.median([r['query_cpu_seconds'] for r in runs]))}
report['identical_outputs']=report['variants']['direct']['runs'][0]['output_sha256']==report['variants']['doubling']['runs'][0]['output_sha256']
report['scope']='1001-request validation pilot; initial feasible bounds supplied by earlier architecture oracle, whose construction cost is excluded. No full billion acceptance.'
report['decision']='Retain optional doubling accelerator; macro route coverage/precision still insufficient, do not replace V59.'
(ROOT/('reports/V64-macro-doubling-phase.json' if phase else 'reports/V64-macro-doubling.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
