"""Explore distance-based compute allocation on existing template corrections."""
import json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score


def main():
    training = json.loads((ROOT/'reports/V56-template-correction.json').read_text())
    assert training['state'] == 'complete'
    x, y, _, _ = load('validation')
    d = x[:, 6]+x[:, 7]
    predictions = {n: np.load(ROOT/f'out/v56/correction-{n}.npy') for n in (128, 256, 512, 1024)}
    report = {'fit_split': 'development', 'gate_selection_split': 'validation', 'holdout_used': False,
              'scope': 'Offline mixed tree-prefix prediction; live throughput pending; reused validation selection',
              'candidates': []}
    for near in (20, 50, 100):
        for middle in (100, 150, 200, 250):
            if near >= middle:
                continue
            for far_trees in (128, 256):
                counts = np.where(d < near, 1024, np.where(d < middle, 512, far_trees))
                pred = np.where(d < near, predictions[1024], np.where(d < middle, predictions[512], predictions[far_trees]))
                item = {'near_distance': near, 'middle_distance': middle, 'far_trees': far_trees,
                        'score': score(y, pred), 'mean_trees': float(counts.mean()),
                        'rows_by_tree_count': {str(n): int(np.sum(counts == n)) for n in (128, 256, 512, 1024)}}
                report['candidates'].append(item)
    report['best'] = max(report['candidates'], key=lambda item: item['score'])
    (ROOT/'reports/V58-adaptive-trees-selection.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['best']))


if __name__ == '__main__':
    main()
