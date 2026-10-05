"""Validation-selected distance gates between existing, development-trained models."""
import csv
import json
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score


def main():
    x, y, _, _ = load('validation')
    d = x[:, 6]+x[:, 7]
    baseline = np.load(ROOT/'out/v50/validation-10-256.npy')
    v51 = json.loads((ROOT/'reports/V51-cpp-architecture-comparison.json').read_text())
    assert v51['state'] == 'complete'
    report = {'fit_split': 'development', 'gate_selection_split': 'validation',
              'holdout_used': False, 'baseline_score': score(y, baseline),
              'scope': 'Exploratory gate selection on reused validation; CPU not yet measured',
              'candidates': []}
    for model in v51['candidates']:
        h, r = model['hidden'], model['routes']
        with (ROOT/f'out/evaluation/validation.v51-h{h}-r{r}.csv').open() as f:
            route = np.array([int(row['delay']) for row in csv.DictReader(f)])
        for threshold in (50, 100, 150, 200, 250, 300):
            pred = np.where(d >= threshold, route, baseline)
            item = {'hidden': h, 'routes': r, 'route_min_distance': threshold,
                    'score': score(y, pred), 'route_rows': int(np.sum(d >= threshold)),
                    'route_model': model['model']}
            report['candidates'].append(item)
    report['best'] = max(report['candidates'], key=lambda item: item['score'])
    (ROOT/'reports/V53-distance-mixture.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['best']))


if __name__ == '__main__':
    main()
