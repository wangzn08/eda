"""V3 prototype: topology-inspired route signatures and selective correction.

Fits only development residuals; evaluates candidates only on validation.
"""
import collections
import json
import math
import time

from architecture import ROOT
from experiment_displacement import weighted_score
from experiment_region_port import load


def blocked_band(y):
    return y // 100 if y < 550 and y % 100 < 50 else -1


def route_class(row):
    sx, sy, tx, ty, *_ = row
    crosses = min(sx, tx) <= 89 and max(sx, tx) >= 76
    if not crosses:
        return 0, 0
    bs, bt = blocked_band(sy), blocked_band(ty)
    if bs < 0 and bt < 0:
        return 0, 0
    if bs != bt:
        return 1, 0
    lower, upper = bs * 100, bs * 100 + 49
    # A route entirely inside one obstructed band must cross or detour.
    detour = min(sy - lower + ty - lower + 2,
                 2 * upper - sy - ty + 2)
    return 2, min(9, max(0, detour // 10))


def key(row, kind):
    sx, sy, tx, ty, sp, tp, _, _ = row
    dx, dy = tx - sx, ty - sy
    direction = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))
    distance = abs(dx) + abs(dy)
    bucket = 0 if distance < 16 else 1 if distance < 64 else 2 if distance < 256 else 3
    route, detour = route_class(row)
    if kind == 'route_distance':
        return route, detour, bucket, *direction
    if kind == 'route_ports':
        return route, detour, sp[0], tp[0], bucket
    if kind == 'wire_phase':
        return sx % 10, tx % 10, sy % 12, ty % 12, bucket
    if kind == 'source_wire_phase':
        return sx % 10, sy % 12, bucket, *direction
    if kind == 'target_wire_phase':
        return tx % 10, ty % 12, bucket, *direction
    if kind == 'route_wire_phase':
        return route, sx % 10, tx % 10, bucket
    raise ValueError(kind)


def risk_group(row):
    distance = abs(row[2]-row[0]) + abs(row[3]-row[1])
    return (0 if distance < 16 else 1 if distance < 64 else 2 if distance < 256 else 3,
            route_class(row)[0])


def fit(rows, kind, prior):
    sums = collections.defaultdict(lambda: [0., 0])
    for row in rows:
        truth, base = row[6:]
        if truth == 0:
            continue
        item = sums[key(row, kind)]
        item[0] += truth - base
        item[1] += 1
    return {k: total / (count + prior) for k, (total, count) in sums.items()}


def score(rows, kind=None, table=None, gate=None):
    total, selected, selected_loss = 0., 0, 0.
    for row in rows:
        truth, base = row[6:]
        if truth == 0:
            continue
        use = kind is not None and (gate is None or gate(row))
        pred = max(0, round(base + table.get(key(row, kind), 0))) if use else base
        loss = 100 - weighted_score(truth, pred)
        total += loss
        if use:
            selected += 1
            selected_loss += loss
    return {'score': 100 - total / len(rows), 'selected_rows': selected,
            'selected_fraction': selected / len(rows),
            'selected_score': 100 - selected_loss / selected if selected else None}


def main():
    start = time.monotonic()
    dev, val = load('development', 'v2'), load('validation', 'v2')
    baseline = score(val)
    candidates = []
    for kind in ('route_distance', 'route_ports', 'wire_phase',
                 'source_wire_phase', 'target_wire_phase', 'route_wire_phase'):
        for prior in (20, 100):
            table = fit(dev, kind, prior)
            result = score(val, kind, table)
            candidates.append({'kind': kind, 'prior': prior, 'entries': len(table), **result})
    chosen = max(candidates, key=lambda x: x['score'])
    table = fit(dev, chosen['kind'], chosen['prior'])
    # Confidence gate uses only geometry and development-derived risk; no
    # validation labels influence the gate itself.
    bins = collections.defaultdict(lambda: [0., 0])
    for row in dev:
        truth, base = row[6:]
        if truth <= 0:
            continue
        group = risk_group(row)
        bins[group][0] += abs(base - truth) / truth
        bins[group][1] += 1
    risk = {k: total / count for k, (total, count) in bins.items()}
    gated = []
    for threshold in (.01, .02, .03, .05):
        def gate(row):
            return risk.get(risk_group(row), 0) >= threshold
        gated.append({'threshold': threshold, **score(val, chosen['kind'], table, gate)})
    # Two-fold development crossfit estimates where the new correction helps,
    # rather than assuming high baseline error implies positive benefit.
    folds = (dev[::2], dev[1::2])
    benefit = collections.defaultdict(lambda: [0., 0])
    for train, audit in ((folds[0], folds[1]), (folds[1], folds[0])):
        half_table = fit(train, chosen['kind'], chosen['prior'])
        for row in audit:
            truth, base = row[6:]
            if truth <= 0:
                continue
            corrected = max(0, round(base + half_table.get(key(row, chosen['kind']), 0)))
            group = risk_group(row)
            benefit[group][0] += weighted_score(truth, corrected) - weighted_score(truth, base)
            benefit[group][1] += 1
    mean_benefit = {k: total / count for k, (total, count) in benefit.items()}
    benefit_gated = []
    for threshold in (0., .02, .05, .1):
        def gate(row):
            return mean_benefit.get(risk_group(row), 0) >= threshold
        benefit_gated.append({'threshold': threshold, **score(val, chosen['kind'], table, gate)})
    report = {'hypothesis': 'Topology-based route sketch and confidence-gated residual',
              'development_rows': len(dev), 'validation_rows': len(val),
              'baseline': baseline, 'candidates': candidates, 'selected_candidate': chosen,
              'development_risk_by_geometry': {str(k): v for k, v in sorted(risk.items())},
              'gated_candidates': gated, 'elapsed_seconds': time.monotonic()-start,
              'crossfit_benefit_by_geometry': {str(k): v for k, v in sorted(mean_benefit.items())},
              'benefit_gated_candidates': benefit_gated,
              'holdout_used': False}
    (ROOT/'reports/V3-route-confidence.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'baseline': baseline, 'best': chosen, 'gated': gated,
                      'benefit_gated': benefit_gated,
                      'seconds': report['elapsed_seconds']}, indent=2))


if __name__ == '__main__':
    main()
