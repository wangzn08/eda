"""Break down V2 validation loss without reading the final holdout split."""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from architecture import ROOT


def endpoint(text):
    site, port = text.split('/', 1)
    _, x, y = site.split('_')
    return int(x), int(y), 'INTER' if port[0] in 'IZ' else 'LOGIC'


def summarize(group):
    return {'rows': group['n'], 'score': 100 - group['loss'] / group['n'],
            'mean_signed_error': group['signed'] / group['n'],
            'share_of_total_score_loss': group['loss']}


def main():
    golden = ROOT / 'out/evaluation/validation.golden.csv'
    prediction = ROOT / 'out/evaluation/validation.v2.csv'
    groups = defaultdict(lambda: {'n': 0, 'loss': 0.0, 'signed': 0.0})
    examples = []
    total = 0
    with golden.open(newline='') as a, prediction.open(newline='') as b:
        for expected, actual in zip(csv.DictReader(a), csv.DictReader(b)):
            if (expected['From'], expected['To']) != (actual['From'], actual['To']):
                raise ValueError('Request order differs')
            truth, estimate = int(expected['delay']), int(actual['delay'])
            if truth == 0:
                continue
            sx, sy, st = endpoint(expected['From'])
            tx, ty, tt = endpoint(expected['To'])
            distance = abs(tx - sx) + abs(ty - sy)
            distance_bucket = '0-15' if distance < 16 else '16-63' if distance < 64 else '64-255' if distance < 256 else '256+'
            relative = abs(estimate - truth) / truth
            error_bucket = '<1%' if relative < .01 else '1-2%' if relative < .02 else '2-5%' if relative < .05 else '5-10%' if relative < .1 else '10-20%' if relative < .2 else '20%+'
            loss = 100 * math.tanh(4 * relative)
            signed = (estimate - truth) / truth
            for category, key in (('overall', 'all'), ('distance', distance_bucket),
                                  ('endpoint_type', f'{st}->{tt}'), ('error', error_bucket)):
                g = groups[(category, key)]
                g['n'] += 1
                g['loss'] += loss
                g['signed'] += signed
            examples.append((loss, expected['From'], expected['To'], truth, estimate))
            total += 1
    if total != 150053:
        raise ValueError(f'Unexpected validation row count: {total}')
    result = {'dataset': 'validation', 'rows': total,
              'groups': {category: {key: {**summarize(value),
                        'share_of_total_score_loss': value['loss'] / total}
                        for (kind, key), value in sorted(groups.items()) if kind == category}
                        for category in ('overall', 'distance', 'endpoint_type', 'error')},
              'highest_loss_examples': [dict(zip(('loss', 'from', 'to', 'golden', 'prediction'), row))
                                        for row in sorted(examples, reverse=True)[:20]]}
    path = ROOT / 'reports/V2-validation-diagnosis.json'
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result['groups'], indent=2))


if __name__ == '__main__':
    main()
