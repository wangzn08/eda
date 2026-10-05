"""Validation error slices for fast architectures; never reads holdout."""
import json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load


def describe(y, pred, mask):
    n = int(mask.sum())
    if not n:
        return {'rows': 0}
    rel = np.abs(pred[mask] - y[mask]) / np.maximum(y[mask], 1)
    loss = np.tanh(4 * rel)
    return {'rows': n, 'score': float(100 * (1 - loss.mean())),
            'mean_absolute_ps': float(np.abs(pred[mask] - y[mask]).mean()),
            'total_score_loss': float(loss.sum()),
            'exact_fraction': float(np.mean(pred[mask] == y[mask]))}


def main():
    x, y, _, _ = load('validation')
    candidates = {'V50-256': ROOT/'out/v50/validation-10-256.npy'}
    train = json.loads((ROOT/'reports/V51-tiny-routes.json').read_text())
    best = train['best']
    candidates['V51-current-best'] = ROOT/best['weights'].replace('.pt', '.npy')
    distance = x[:, 6] + x[:, 7]
    groups = {'all': np.ones(len(y), dtype=bool)}
    for lo, hi in [(0, 20), (20, 50), (50, 100), (100, 200), (200, 10000)]:
        groups[f'manhattan_{lo}_{hi}'] = (distance >= lo) & (distance < hi)
    for rx in range(10):
        for ry in range(12):
            groups[f'effective_phase_{rx}_{ry}'] = (x[:, 35] % 10 == rx) & (x[:, 36] % 12 == ry)
    report = {'split': 'validation', 'holdout_used': False,
              'purpose': 'Architecture diagnosis only; validation selection is optimistic',
              'v51_checkpoint': best, 'models': {}}
    for name, path in candidates.items():
        pred = np.load(path)
        slices = {k: describe(y, pred, mask) for k, mask in groups.items()}
        report['models'][name] = {'prediction_file': str(path.relative_to(ROOT)),
                                'slices': slices,
                                'worst_phases_by_total_loss': sorted(
                                    [dict(group=k, **v) for k, v in slices.items() if k.startswith('effective_phase')],
                                    key=lambda item: item['total_score_loss'], reverse=True)[:12]}
    dest = ROOT/'reports/fast-error-slices.json'
    dest.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v['slices']['all'] for k, v in report['models'].items()}))


if __name__ == '__main__':
    main()
