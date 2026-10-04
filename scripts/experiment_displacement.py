"""P4 exploratory displacement table; train on development, score validation only.

This is deliberately a fast approximate oracle, not the submitted estimator.
It never reads the holdout split or labels at prediction time.
"""
import collections
import csv
import json
import math
import re
import time
from pathlib import Path

from architecture import ROOT


PATTERN = re.compile(r'^SRB_(\d+)_(\d+)/(.+)$')
DATA = ROOT / 'out/evaluation'


def parse(row):
    source = PATTERN.fullmatch(row['From'])
    target = PATTERN.fullmatch(row['To'])
    if source is None or target is None:
        raise ValueError('Unexpected endpoint')
    sx, sy, sp = source.groups()
    tx, ty, tp = target.groups()
    dx, dy = int(tx) - int(sx), int(ty) - int(sy)
    return dx, dy, sp, tp, int(row['delay'])


def bucket(dx, dy, width_x, width_y):
    return ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0),
            abs(dx) // width_x, abs(dy) // width_y)


def weighted_score(golden, pred):
    if golden == 0:
        return None
    return 100 * (1 - math.tanh(4 * abs(pred - golden) / golden))


def quantile(sorted_values, fraction):
    return sorted_values[min(len(sorted_values) - 1, math.ceil(len(sorted_values) * fraction) - 1)]


def train(rows, width_x, width_y, prior=16, weight_power=0):
    # The geometric baseline prevents empty and sparse bins from returning zero.
    # Within each displacement bin, endpoint port offsets are learned only from
    # the residual. Two backfitting rounds avoid source/target bias leakage.
    total, xsum, ysum, xx, yy, xy, gx, gy, dsum = [0.0] * 9
    for dx, dy, _, _, d in rows:
        weight = (1000 / max(100, d)) ** weight_power
        x, y = abs(dx), abs(dy)
        total += weight; xsum += weight*x; ysum += weight*y
        xx += weight*x*x; yy += weight*y*y; xy += weight*x*y
        gx += weight*x*d; gy += weight*y*d; dsum += weight*d
    mean_d = dsum / total
    mx, my = xsum / total, ysum / total
    vx, vy, covariance = xx / total - mx*mx, yy / total - my*my, xy / total - mx*my
    rhs_x, rhs_y = gx / total - mx*mean_d, gy / total - my*mean_d
    determinant = vx*vy - covariance*covariance
    ax = (rhs_x*vy - rhs_y*covariance) / determinant
    ay = (rhs_y*vx - rhs_x*covariance) / determinant
    intercept = mean_d - ax*mx - ay*my
    source_offsets, target_offsets, table = {}, {}, {}
    for _ in range(3):
        sums = collections.defaultdict(lambda: [0.0, 0])
        for dx, dy, sp, tp, d in rows:
            weight = (1000 / max(100, d)) ** weight_power
            key = bucket(dx, dy, width_x, width_y)
            baseline = intercept + ax*abs(dx) + ay*abs(dy)
            sums[key][0] += weight * (d - baseline - source_offsets.get(sp, 0) - target_offsets.get(tp, 0))
            sums[key][1] += weight
        table = {k: value / (count + prior) for k, (value, count) in sums.items()}
        for port_index, current, other in ((2, source_offsets, target_offsets), (3, target_offsets, source_offsets)):
            sums = collections.defaultdict(lambda: [0.0, 0])
            for dx, dy, sp, tp, d in rows:
                weight = (1000 / max(100, d)) ** weight_power
                key = bucket(dx, dy, width_x, width_y)
                own, opposite = (sp, tp) if port_index == 2 else (tp, sp)
                baseline = intercept + ax*abs(dx) + ay*abs(dy)
                sums[own][0] += weight * (d - baseline - table.get(key, 0) - other.get(opposite, 0))
                sums[own][1] += weight
            current.clear()
            current.update({k: value / (count + prior) for k, (value, count) in sums.items()})
    return intercept, ax, ay, source_offsets, target_offsets, table


def predict(row, model, width_x, width_y):
    dx, dy, sp, tp, _ = row
    intercept, ax, ay, source_offsets, target_offsets, table = model
    if dx == dy == 0 and sp == tp:
        return 0
    estimate = (intercept + ax*abs(dx) + ay*abs(dy)
                + table.get(bucket(dx, dy, width_x, width_y), 0)
                + source_offsets.get(sp, 0) + target_offsets.get(tp, 0))
    return max(0, round(estimate))


def main():
    started = time.monotonic()
    with (DATA / 'development.golden.csv').open(newline='') as f:
        development = [parse(row) for row in csv.DictReader(f)]
    with (DATA / 'validation.golden.csv').open(newline='') as f:
        validation = [parse(row) for row in csv.DictReader(f)]
    reports = []
    for wx, wy in ((2, 4), (4, 8), (1, 2), (8, 16)):
        model = train(development, wx, wy)
        scores, errors = [], []
        zeros = zero_exact = 0
        for row in validation:
            pred = predict(row, model, wx, wy)
            if row[4] == 0:
                zeros += 1; zero_exact += pred == 0
                continue
            scores.append(weighted_score(row[4], pred))
            errors.append(abs(pred-row[4])/row[4])
        errors.sort()
        reports.append({'bin_width_x': wx, 'bin_width_y': wy,
                        'table_entries': len(model[-1]),
                        'score_positive': sum(scores)/len(scores),
                        'relative_error_p50': quantile(errors, .5),
                        'relative_error_p95': quantile(errors, .95),
                        'relative_error_p99': quantile(errors, .99),
                        'zero_golden_rows': zeros, 'zero_exact': zero_exact})
    result = {'method': 'regularized signed displacement residual table + source/target port offsets',
              'reference': 'Marquardt et al. 2000 §3.1; adaptation is experimental, not claimed exact',
              'development_rows': len(development), 'validation_rows': len(validation),
              'elapsed_seconds': time.monotonic()-started, 'results': reports,
              'holdout_used': False}
    (ROOT / 'reports/P4-displacement.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
