"""Validation diagnostics of geometric obstacle strata; no fitting or holdout."""
import csv
import json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load


def main():
    x, y, _, _ = load('validation')
    ax, ay, bx, by = (x[:, i] for i in range(4))
    crossing = (np.minimum(ax, bx) < 76) & (np.maximum(ax, bx) > 89)
    same_band = ay//50 == by//50
    blocked = (ay.astype(int)//50) % 2 == 0
    groups = {'all': np.ones(len(y), dtype=bool), 'no_wall_crossing': ~crossing,
              'cross_same_blocked_band': crossing & same_band & blocked,
              'cross_same_open_band': crossing & same_band & ~blocked,
              'cross_different_bands': crossing & ~same_band}
    report = {'split': 'validation', 'holdout_used': False,
              'scope': 'Geometric endpoint slices only; do not identify actual chosen path', 'models': {}}
    for name, filename in [('template', 'validation.v55-core.csv'),
                           ('template_correction256', 'validation.v56-correction-256.csv'),
                           ('template_correction1024', 'validation.v56-correction-1024.csv'),
                           ('obstacle_correction256', 'validation.v59-correction-256.csv')]:
        with (ROOT/'out/evaluation'/filename).open() as f:
            p = np.array([int(row['delay']) for row in csv.DictReader(f)], dtype=np.float64)
        assert len(p) == len(y)
        rel = np.abs(p-y)/np.maximum(y, 1)
        loss = np.tanh(4*rel)
        slices = {}
        for group, mask in groups.items():
            slices[group] = {'rows': int(mask.sum()), 'score': float(100*(1-loss[mask].mean())),
                             'mean_absolute_ps': float(np.abs(p[mask]-y[mask]).mean()),
                             'total_loss_fraction': float(loss[mask].sum()/loss.sum()),
                             'underprediction_fraction': float(np.mean(p[mask] < y[mask]))}
        report['models'][name] = slices
    (ROOT/'reports/obstacle-error-slices.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
