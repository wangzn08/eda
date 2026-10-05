"""Record actual short A* accuracy and search cost, without billion extrapolation."""
import csv
import json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
x,y,_,_=load('validation')
d=np.abs(x[:,2]-x[:,0])+np.abs(x[:,3]-x[:,1]); mask=d<=20
with (ROOT/'out/evaluation/v60-short20.exact.csv').open() as f:
    p=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
with (ROOT/'out/evaluation/v60-short20.stats.csv').open() as f:
    stats=list(csv.DictReader(f))
assert len(p)==int(mask.sum())==len(stats)
wall=np.array([float(r['wall_ms']) for r in stats])
report={'rows':len(p),'distance_at_most':20,'holdout_used':False,
        'exact_match_fraction':float(np.mean(p==y[mask])),
        'score':float(100*(1-np.tanh(4*np.abs(p-y[mask])/np.maximum(y[mask],1)).mean())),
        'query_wall_seconds_sum':float(wall.sum()/1000),
        'mean_query_wall_microseconds':float(wall.mean()*1000),
        'p99_query_wall_microseconds':float(np.quantile(wall,.99)*1000),
        'mean_settled_states':float(np.mean([int(r['settled']) for r in stats])),
        'process_log':(ROOT/'out/v60-short20.log').read_text().strip(),
        'decision':'Do not integrate distance-only refinement: small score ceiling and costly searches. Explore better mid/long-distance path representation.',
        'limitations':'One validation subset run, wall timings include instrumentation; not official throughput or billion-request acceptance.'}
(ROOT/'reports/V60-short-exact-pilot.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
