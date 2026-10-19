"""Compare native-route residual representations; development fitting only."""
import json
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np

from architecture import ROOT
from selected_physics_interactions import augment, specifications, cpp_header

OUT = ROOT / 'out/v244'
OUT.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / 'reports/V244-native-score-architectures.json'
z = np.load(ROOT / 'out/v125/fit-features.npz')
y, yv = z['y'].astype(float), z['yv'].astype(float)
n, nv = len(y), len(yv)
x = np.memmap(ROOT / 'out/v243/all.features.f32', mode='r', dtype='<f4', shape=(n + nv, 137))
base = np.fromfile(ROOT / 'out/v243/all.base.i32', dtype='<i4').astype(float)
b, bv = base[:n], base[n:]
names = json.loads((ROOT / 'out/v216/features.json').read_text())
report = {'state': 'running', 'fit_scope': 'Native V242 route features; development labels only; validation comparison only',
          'holdout_used': False, 'base_score': None, 'candidates': [],
          'references': [
              'https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html',
              'https://proceedings.mlr.press/r16/wang18c.html',
              'https://www.eecg.utoronto.ca/~vaughn/papers/fpl2016_complex_routing.pdf'],
          'novelty_scope': 'FPGA endpoint/curve interaction and domain-specialist adaptation; existing GBDT and cascades are not claimed as new theory'}


def score(p):
    return float(100 * np.mean(1 - np.tanh(4 * abs(p - yv) / yv)))


def record(item, p):
    item['score'] = score(p)
    item['exact_fraction'] = float(np.mean(p == yv))
    report['candidates'].append(item)
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(item), flush=True)


report['base_score'] = score(bv)
old = lgb.Booster(model_file=str(ROOT / 'out/v216/tree8.txt'))
record({'name': 'full-old8-native', 'trees': 8}, np.rint(np.maximum(0, bv + old.predict(x[n:], num_threads=1))))
params = {'objective': 'regression_l1', 'max_depth': 24, 'min_data_in_leaf': 25,
          'learning_rate': .15, 'num_threads': 1, 'verbosity': -1,
          'force_col_wise': True, 'deterministic': True, 'seed': 20261019}

for representation, leaves in [('plain', 1023), ('physics', 1023), ('physics-small', 511)]:
    enriched = representation.startswith('physics')
    train, valid = (augment(x[:n]), augment(x[n:])) if enriched else (np.asarray(x[:n]), np.asarray(x[n:]))
    feature_names = names + [s[0] for s in specifications()] if enriched else names
    (OUT / f'{representation}.features.json').write_text(json.dumps(feature_names, indent=2) + '\n')
    start = time.monotonic()
    ds = lgb.Dataset(train, label=y - b, weight=1000 / np.maximum(y, 1))
    model = lgb.train({**params, 'num_leaves': leaves}, ds, num_boost_round=64)
    model.save_model(str(OUT / f'{representation}.txt'))
    for trees in (8, 16, 32, 64):
        correction = model.predict(valid, num_iteration=trees, num_threads=1)
        prediction = np.rint(np.maximum(0, bv + correction))
        np.save(OUT / f'{representation}-{trees}.npy', prediction)
        record({'name': representation, 'trees': trees, 'leaves': leaves,
                'features': len(feature_names), 'model': str((OUT / f'{representation}.txt').relative_to(ROOT)),
                'elapsed_seconds': time.monotonic() - start}, prediction)
    del ds, model, train, valid

# Separate experts for crossing the long vertical wall. Each request evaluates
# one expert, not both. No validation labels enter either fit.
start = time.monotonic()
cross, crossv = x[:n, 54] > 0, x[n:, 54] > 0
train, valid = augment(x[:n]), augment(x[n:])
experts = []
for index in (0, 1):
    selected = cross == bool(index)
    ds = lgb.Dataset(train[selected], label=(y - b)[selected],
                     weight=(1000 / np.maximum(y, 1))[selected])
    model = lgb.train({**params, 'num_leaves': 511}, ds, num_boost_round=32)
    model.save_model(str(OUT / f'wall-expert-{index}.txt'))
    experts.append(model)
for trees in (8, 16, 32):
    correction = np.zeros(nv)
    for index, model in enumerate(experts):
        selected = crossv == bool(index)
        correction[selected] = model.predict(valid[selected], num_iteration=trees, num_threads=1)
    prediction = np.rint(np.maximum(0, bv + correction))
    np.save(OUT / f'wall-experts-{trees}.npy', prediction)
    record({'name': 'wall-experts', 'trees_per_request': trees, 'total_trees': 2 * trees,
            'features': train.shape[1], 'leaves_per_tree': 511,
            'elapsed_seconds': time.monotonic() - start}, prediction)

(OUT / 'selected_physics_features.hpp').write_text(cpp_header())
report['state'] = 'complete'
report['best_offline'] = max(report['candidates'], key=lambda v: v['score'])
report['scope'] = 'Offline full validation, not yet the same-candidate native score/speed/memory/package evidence'
REPORT.write_text(json.dumps(report, indent=2) + '\n')
print('best', json.dumps(report['best_offline']), flush=True)
