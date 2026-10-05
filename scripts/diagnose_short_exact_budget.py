"""Measure optimistic score ceilings for exact short-query refinement; validation only."""
import csv
import json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load

x, y, _, _ = load('validation')
with (ROOT/'out/evaluation/validation.v59-profile.csv').open() as f:
    p = np.array([int(r['delay']) for r in csv.DictReader(f)], dtype=np.float64)
assert len(p) == len(y)
d = np.abs(x[:, 2]-x[:, 0])+np.abs(x[:, 3]-x[:, 1])
loss = np.tanh(4*np.abs(p-y)/np.maximum(y, 1))
rows = []
for threshold in (5, 10, 20, 30, 50, 100, 150, 200):
    mask = d <= threshold
    rows.append({'distance_at_most': threshold, 'rows': int(mask.sum()),
                 'fraction': float(mask.mean()),
                 'optimistic_score_if_all_selected_exact': float(100*(1-loss[~mask].sum()/len(y))),
                 'remaining_loss_fraction': float(loss[~mask].sum()/loss.sum())})
report = {'baseline_score': float(100*(1-loss.mean())), 'holdout_used': False,
          'scope': 'Optimistic ceiling replaces selected predictions with golden values; not achieved accuracy or runtime.',
          'thresholds': rows}
(ROOT/'reports/V60-short-exact-ceilings.json').write_text(json.dumps(report, indent=2)+'\n')
with (ROOT/'out/evaluation/validation.request.csv').open() as src, (ROOT/'out/evaluation/v60-short20.request.csv').open('w') as dst:
    reader = csv.reader(src); writer = csv.writer(dst); writer.writerow(next(reader))
    for row, keep in zip(reader, d <= 20):
        if keep: writer.writerow(row)
print(json.dumps(report, indent=2))
