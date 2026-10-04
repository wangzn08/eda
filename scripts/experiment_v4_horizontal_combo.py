"""Evaluate sequential horizontal residual corrections after the frozen V4 tables."""
import json
import time

from architecture import ROOT
from experiment_region_port import load
from experiment_v4_interactions import fit, key, score


def apply(rows, kind, table):
    return [(*row[:7], max(0, round(row[7] + table.get(key(row, kind), 0)))) for row in rows]


def main():
    start = time.monotonic()
    dev = load('development', 'v4-table')
    val = load('validation', 'v4-table')
    baseline = score(val, 'target_port_dx8', {})
    orders = (
        ('target_port_dx8', 'source_port_dx8'),
        ('source_port_dx8', 'target_port_dx8'),
        ('target_port_dx8', 'signed_dx_dybucket'),
        ('signed_dx_dybucket', 'target_port_dx8'),
        ('target_port_dx8', 'source_port_dx8', 'signed_dx_dybucket'),
        ('signed_dx_dybucket', 'target_port_dx8', 'source_port_dx8'),
        ('target_port_dx8', 'source_port_x'),
    )
    results = []
    for order in orders:
        training, validation = dev, val
        stages = []
        for kind in order:
            table = fit(training, kind, 20)
            training = apply(training, kind, table)
            validation = apply(validation, kind, table)
            stages.append({'kind': kind, 'entries': len(table),
                           'validation_score': score(validation, kind, {})})
        results.append({'order': order, 'stages': stages})
        print(results[-1], flush=True)
    report = {'baseline': baseline, 'candidates': results,
              'elapsed_seconds': time.monotonic()-start, 'holdout_used': False}
    (ROOT/'reports/V4-horizontal-combo.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
