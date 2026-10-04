"""P4 experiment: geometry residual corrections on top of displacement table.

Feature definitions come only from SRB_Gap.json and endpoint coordinates.
Golden delays are used solely while fitting on the development partition.
"""
import collections
import csv
import json
import math
import time

from architecture import DEFAULT_ARCH, ROOT
from experiment_displacement import DATA, PATTERN, parse, predict, train, weighted_score, quantile


def read_rows(path):
    rows = []
    with path.open(newline='') as f:
        for record in csv.DictReader(f):
            base = parse(record)
            sx, sy, _ = PATTERN.fullmatch(record['From']).groups()
            tx, ty, _ = PATTERN.fullmatch(record['To']).groups()
            rows.append((base, int(sx), int(sy), int(tx), int(ty)))
    return rows


def spans(a, b, site):
    return min(a, b) <= site < max(a, b)


def geometry_features(row, gaps):
    _, sx, sy, tx, ty = row
    features = []
    for line in gaps['Line']:
        a, b = (sx, tx) if line['direction'] == 'vertical' else (sy, ty)
        if spans(a, b, line['site']):
            features.append(('line', line['id']))
    # Endpoint bounding-box intersects a physical block. This is a cheap
    # proxy, not a claim that the true shortest path traverses that block.
    for block in gaps['Block']:
        if (max(sx, tx) >= block['left'] and min(sx, tx) <= block['right']
                and max(sy, ty) >= block['lower'] and min(sy, ty) <= block['upper']):
            features.append(('block', block['id']))
    return features


def fit_corrections(rows, base_model, features, prior):
    # Residual mean per active feature, backfitted with shrinkage. Unlike
    # fitting one multivariate table, this remains small and sparse.
    baseline = [predict(row[0], base_model, 8, 16) for row in rows]
    offsets = {}
    for _ in range(10):
        sums = collections.defaultdict(lambda: [0.0, 0])
        for row, base, active in zip(rows, baseline, features):
            rest = row[0][4] - base - sum(offsets.get(f, 0) for f in active)
            for f in active:
                sums[f][0] += rest + offsets.get(f, 0)
                sums[f][1] += 1
        # Many crossed lines co-occur. Simultaneous full updates are unstable;
        # damp each Jacobi update to preserve the additive model.
        offsets = {f: 0.8 * offsets.get(f, 0) + 0.2 * total / (count + prior)
                   for f, (total, count) in sums.items()}
    return offsets


def score(rows, model, features, offsets):
    scores, errors = [], []
    by_group = collections.defaultdict(list)
    for row, active in zip(rows, features):
        golden = row[0][4]
        prediction = max(0, round(predict(row[0], model, 8, 16) + sum(offsets.get(f, 0) for f in active)))
        if golden == 0:
            continue
        value = weighted_score(golden, prediction)
        scores.append(value)
        errors.append(abs(prediction-golden)/golden)
        by_group['has_block' if any(f[0] == 'block' for f in active) else 'no_block'].append(value)
        by_group['short' if abs(row[0][0])+abs(row[0][1]) <= 20 else 'long'].append(value)
    errors.sort()
    return {'positive_score': sum(scores)/len(scores),
            'relative_error_p50': quantile(errors, .5),
            'relative_error_p95': quantile(errors, .95),
            'relative_error_p99': quantile(errors, .99),
            'groups': {key: {'rows': len(values), 'score': sum(values)/len(values)}
                       for key, values in by_group.items()}}


def main():
    started = time.monotonic()
    gaps = json.loads((DEFAULT_ARCH / 'SRB_Gap.json').read_text())['Gap']
    development = read_rows(DATA / 'development.golden.csv')
    validation = read_rows(DATA / 'validation.golden.csv')
    dev_features = [geometry_features(row, gaps) for row in development]
    val_features = [geometry_features(row, gaps) for row in validation]
    model = train([row[0] for row in development], 8, 16)
    candidates = []
    for prior in (100, 1000):
        offsets = fit_corrections(development, model, dev_features, prior)
        candidates.append({'prior': prior, 'features': len(offsets),
                           'metrics': score(validation, model, val_features, offsets)})
    report = {'development_rows': len(development), 'validation_rows': len(validation),
              'baseline': score(validation, model, val_features, {}),
              'candidates': candidates, 'elapsed_seconds': time.monotonic()-started,
              'holdout_used': False,
              'caveat': 'Endpoint bounding-box features do not identify the true routing path.'}
    (ROOT / 'reports/P4-gap-features.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
