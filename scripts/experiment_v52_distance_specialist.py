"""Development-only short/mid-distance residual experts; validation selection."""
import argparse
import json
import time
import numpy as np
from catboost import CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features, lower
from experiment_v7_teacher import score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait-v51', action='store_true')
    args = parser.parse_args()
    if args.wait_v51:
        ready = ROOT/'reports/V51-factor-architecture-comparison.json'
        while not ready.exists() or json.loads(ready.read_text()).get('state') != 'complete':
            print('Waiting for V51 factor throughput measurements', flush=True)
            time.sleep(30)
    folder = ROOT/'out/v52'
    folder.mkdir(exist_ok=True)
    x, y, _, _ = load('development')
    xv, yv, _, _ = load('validation')
    lo, lv = lower('development'), lower('validation')
    a, av = features(x, lo), features(xv, lv)
    base = np.load(ROOT/'out/v50/validation-10-256.npy')
    d, dv = x[:, 6] + x[:, 7], xv[:, 6] + xv[:, 7]
    report = {'fit_split': 'development', 'selection_split': 'validation',
              'holdout_used': False, 'baseline_score': score(yv, base),
              'scope': 'Distance specialists anchored at the same PDB; CPU export pending',
              'candidates': []}
    for ceiling in (50, 100, 200):
        mask = (d < ceiling) & (y > 0)
        vm = dv < ceiling
        model = CatBoostRegressor(iterations=512, depth=8, learning_rate=.07,
                                 loss_function='MAE', thread_count=2, random_seed=20261007,
                                 l2_leaf_reg=5, verbose=128, allow_writing_files=False)
        model.fit(a[mask], (y[mask]-lo[mask])/100,
                  sample_weight=1/np.maximum(y[mask], 1))
        model.save_model(str(folder/f'distance-{ceiling}.json'), format='json')
        for trees in (64, 128, 256, 512):
            pred = base.copy()
            pred[vm] = np.rint(lv[vm] + np.maximum(
                0, 100*model.predict(av[vm], ntree_end=trees, thread_count=2)))
            name = f'distance-{ceiling}-{trees}'
            np.save(folder/f'{name}.npy', pred)
            item = {'ceiling': ceiling, 'trees': trees, 'training_rows': int(mask.sum()),
                    'validation_rows_routed': int(vm.sum()), 'score': score(yv, pred)}
            report['candidates'].append(item)
            print(json.dumps(item), flush=True)
        report['best'] = max(report['candidates'], key=lambda item: item['score'])
        (ROOT/'reports/V52-distance-specialist.json').write_text(json.dumps(report, indent=2)+'\n')
    report['state'] = 'complete'
    (ROOT/'reports/V52-distance-specialist.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
