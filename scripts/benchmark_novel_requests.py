"""Measure frozen V242 on distinct, newly recombined request pairs.

Only development request pins and validation request pairs are read. No labels
or holdout data are read; this is a synthetic throughput measurement, not a
generalization score or a prediction of the official hidden input distribution.
"""
import argparse
import csv
import gc
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import time

import numpy as np

from architecture import ROOT


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, report):
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')


def generate(folder, count, runs, seed):
    with (ROOT / 'out/evaluation/development.request.csv').open() as stream:
        development = [(r['From'], r['To']) for r in csv.DictReader(stream)]
    sources = sorted({s for s, _ in development})
    targets = sorted({t for _, t in development})
    source_id = {s: i for i, s in enumerate(sources)}
    target_id = {t: i for i, t in enumerate(targets)}
    width = len(targets)
    sid = np.array([source_id[s] for s, _ in development], dtype=np.int64)
    tid = np.array([target_id[t] for _, t in development], dtype=np.int64)
    forbidden = set((sid * width + tid).tolist())
    with (ROOT / 'out/evaluation/validation.request.csv').open() as stream:
        for row in csv.DictReader(stream):
            s, t = source_id.get(row['From']), target_id.get(row['To'])
            if s is not None and t is not None:
                forbidden.add(s * width + t)
    forbidden = np.array(sorted(forbidden), dtype=np.int64)
    rng = np.random.default_rng(seed)
    required = count * runs
    pairs = np.empty(0, dtype=np.int64)
    while len(pairs) < required:
        number = int((required - len(pairs)) * 1.03) + 1024
        new_pairs = (
            sid[rng.integers(len(development), size=number)] * width
            + tid[rng.integers(len(development), size=number)]
        )
        pairs = np.unique(np.concatenate((pairs, new_pairs)))
        pairs = pairs[~np.isin(pairs, forbidden, assume_unique=True)]
    rng.shuffle(pairs)
    pairs = pairs[:required]
    assert len(np.unique(pairs)) == required
    assert not np.isin(pairs, forbidden, assume_unique=True).any()
    inventory = []
    for run in range(runs):
        path = folder / f'novel-{run + 1}.request.csv'
        selected = pairs[run * count:(run + 1) * count]
        with path.open('w') as stream:
            stream.write('From,To\n')
            for begin in range(0, count, 20000):
                stream.writelines(
                    f'{sources[int(p) // width]},{targets[int(p) % width]}\n'
                    for p in selected[begin:begin + 20000]
                )
        item = {'path': str(path.relative_to(ROOT)), 'rows': count,
                'bytes': path.stat().st_size, 'sha256': digest(path)}
        inventory.append(item)
        print(json.dumps({'phase': 'generated', **item}), flush=True)
    return {
        'seed': seed, 'numpy_version': np.__version__,
        'development_rows': len(development),
        'distinct_source_pins': len(sources), 'distinct_target_pins': len(targets),
        'method': 'Independent empirical development source and target marginals; '
                  'reject all development/validation pairs and duplicates; shuffle; '
                  'disjoint sequential slices for separate fresh processes',
        'distinct_pairs_across_all_runs': required,
        'known_development_validation_pairs_present': 0,
        'duplicate_pairs_across_all_runs': 0,
        'labels_read': False, 'holdout_read': False, 'files': inventory,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows-per-run', type=int, default=3000000)
    parser.add_argument('--runs', type=int, default=2)
    parser.add_argument('--seed', type=int, default=20261019)
    parser.add_argument('--directory', default='out/runtime-kernel-v242')
    parser.add_argument('--output-directory', default='out/v242/novel-requests')
    parser.add_argument('--report', default='reports/V242-novel-request-profile.json')
    args = parser.parse_args()
    assert args.rows_per_run > 0 and args.runs > 0
    folder = ROOT / args.output_directory
    folder.mkdir(parents=True, exist_ok=True)
    report_path = ROOT / args.report
    runtime = ROOT / args.directory
    assets = {p.name: digest(p) for p in runtime.iterdir() if p.is_file()}
    frozen = json.loads((ROOT / 'reports/V242-joint-goal-profile.json').read_text())
    assert assets == frozen['asset_sha256_before'], 'Frozen V242 runtime changed'
    report = {
        'state': 'generating', 'platform': platform.platform(),
        'machine': platform.machine(), 'runtime': args.directory,
        'asset_sha256_before': assets, 'prediction_cache': False,
        'architecture_operator_cache': True,
        'scope': 'Synthetic distinct recombined development pins, Apple M4/macOS, '
                 'same frozen V242, standard CSV I/O, serial fresh processes; '
                 'not official hidden requests, no accuracy labels available',
        'extrapolation': 'initialization_cpu + 1e9 * query_cpu / measured_rows; '
                         'assumes comparable distribution and sustained throughput',
        'runs': [],
    }
    save(report_path, report)
    report['input_inventory'] = generate(folder, args.rows_per_run, args.runs, args.seed)
    gc.collect()  # Release generation arrays before the measured runtime starts.
    report['state'] = 'measuring'
    save(report_path, report)
    for index, input_item in enumerate(report['input_inventory']['files'], 1):
        source = ROOT / input_item['path']
        destination = folder / f'novel-{index}.output.csv'
        log = folder / f'novel-{index}.stderr'
        command = [str(runtime / 'estimate'), '-in', str(source), '-out', str(destination)]
        print(json.dumps({'phase': 'running', 'index': index, 'rows': args.rows_per_run}), flush=True)
        start = time.monotonic()
        with log.open('w') as stream:
            process = subprocess.run(['/usr/bin/time', '-l', *command],
                                     cwd=ROOT, stderr=stream, timeout=1800)
        wall = time.monotonic() - start
        text = log.read_text()
        assert process.returncode == 0, text
        cpu = float(re.search(r'cpu_seconds=([0-9.]+)', text)[1])
        initialization = float(re.search(r'initialization_seconds=([0-9.]+)', text)[1])
        rows = int(re.search(r'rows=(\d+)', text)[1])
        assert rows == args.rows_per_run
        match = re.search(r'architecture_operator_cache_bytes=(\d+) hits=(\d+) misses=(\d+) final_prediction_cache=0', text)
        assert match
        hits, misses = int(match[2]), int(match[3])
        counted = nonfinite = 0
        minimum, maximum = 10**18, -10**18
        with source.open() as inputs, destination.open() as outputs:
            a, b = csv.DictReader(inputs), csv.DictReader(outputs)
            for source_row, result in zip(a, b, strict=True):
                assert (source_row['From'], source_row['To']) == (result['From'], result['To'])
                value = int(result['delay'])
                minimum, maximum = min(minimum, value), max(maximum, value)
                nonfinite += value < 0 or value >= 1000000000
                counted += 1
        assert counted == rows and nonfinite == 0
        query = cpu - initialization
        item = {
            'index': index, 'rows': rows, 'command': command,
            'total_cpu_seconds': cpu, 'initialization_cpu_seconds': initialization,
            'query_cpu_seconds': query, 'total_wall_seconds': wall,
            'query_cpu_seconds_per_request': query / rows,
            'query_cpu_microseconds_per_request': query / rows * 1e6,
            'billion_estimate_cpu_seconds_including_initialization': initialization + query / rows * 1e9,
            'maximum_rss_bytes': int(re.search(r'(\d+)\s+maximum resident set size', text)[1]),
            'operator_hits': hits, 'operator_misses': misses,
            'operator_hit_fraction': hits / (hits + misses),
            'output_rows_and_pin_order_verified': True,
            'invalid_or_unreachable_output_rows': nonfinite,
            'minimum_delay': minimum, 'maximum_delay': maximum,
            'output_sha256': digest(destination),
            'stderr': str(log.relative_to(ROOT)),
        }
        report['runs'].append(item)
        save(report_path, report)
        print(json.dumps({'phase': 'complete', **item}), flush=True)
    after = {p.name: digest(p) for p in runtime.iterdir() if p.is_file()}
    assert after == assets
    report['asset_sha256_after'] = after
    report['state'] = 'complete'
    total_query = sum(r['query_cpu_seconds'] for r in report['runs'])
    total_rows = sum(r['rows'] for r in report['runs'])
    average_init = sum(r['initialization_cpu_seconds'] for r in report['runs']) / args.runs
    report['pooled_query_cpu_seconds_per_request'] = total_query / total_rows
    report['pooled_billion_estimate_cpu_seconds_including_initialization'] = average_init + total_query / total_rows * 1e9
    save(report_path, report)
    print(json.dumps({'phase': 'all-complete',
                      'seconds_per_request': total_query / total_rows,
                      'billion_seconds': average_init + total_query / total_rows * 1e9}), flush=True)


if __name__ == '__main__':
    main()
