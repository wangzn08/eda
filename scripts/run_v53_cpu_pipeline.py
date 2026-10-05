"""Measure single-model-per-query distance mixtures after V52 CPU measurements."""
import argparse
import csv
import json
import os
import re
import time
import numpy as np
from architecture import ROOT
from run_v51_pipeline import run
from architecture_benchmark_data import load


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', required=True, type=int)
    args = p.parse_args()
    waiting = ROOT/'reports/V52-cpu-comparison.json'
    while not waiting.exists() or json.loads(waiting.read_text()).get('state') != 'complete':
        try:
            os.kill(args.wait_pid, 0)
        except ProcessLookupError:
            raise RuntimeError('Prior CPU pipeline ended before completion')
        time.sleep(30)
    python = str(ROOT/'out/research-env/bin/python')
    folder = ROOT/'out/v53'
    folder.mkdir(exist_ok=True)
    selection = json.loads((ROOT/'reports/V53-distance-mixture.json').read_text())
    x, _, _, _ = load('validation')
    d = x[:, 6]+x[:, 7]
    base = np.load(ROOT/'out/v50/validation-10-256.npy')
    report = {'state': 'running', 'holdout_used': False,
              'scope': 'Validation-selected mixtures; no per-query certificates; billion CPU is extrapolated',
              'candidates': []}
    for h, r in ((64, 128), (128, 128), (64, 64)):
        chosen = max((c for c in selection['candidates'] if c['hidden'] == h and c['routes'] == r),
                     key=lambda c: c['score'])
        name = f'h{h}-r{r}-d{chosen["route_min_distance"]}'
        route_path = ROOT/chosen['route_model']
        binary, bounds = ROOT/'build/phase_fast_estimate', ROOT/'models/phase-bounds-safe.bin'
        base_path = ROOT/'models/fast-residual-v50.bin'
        command = [str(binary), '--phase-bounds', str(bounds), '--residual-model', str(base_path),
                   '--trees', '256', '--route-model', str(route_path), '--route-min-distance',
                   str(chosen['route_min_distance']), '--no-cache']
        pred = ROOT/f'out/evaluation/validation.v53-{name}.csv'
        log = folder/f'{name}-validation.log'
        run(['/usr/bin/time', '-l', *command, '-in', str(ROOT/'out/evaluation/validation.request.csv'),
             '-out', str(pred)], log)
        run([python, 'scripts/evaluate_fast_phase.py', '--name', f'V53-{name}-cpp',
             '--prediction', str(pred.relative_to(ROOT)), '--log', str(log.relative_to(ROOT))],
            folder/f'{name}-evaluation.log')
        evaluation = json.loads((ROOT/f'reports/V53-{name}-cpp.json').read_text())
        def delays(path):
            with path.open() as f:
                return np.array([int(row['delay']) for row in csv.DictReader(f)])
        reference = np.where(d >= chosen['route_min_distance'],
                             delays(ROOT/f'out/evaluation/validation.v51-h{h}-r{r}.csv'), base)
        diff = np.abs(delays(pred)-reference)
        assert diff.max() <= 1, 'Mixed implementation deviates by more than 1ps'
        speedlog = folder/f'{name}-speed10m.log'
        run(['/usr/bin/time', '-l', *command, '-in', str(ROOT/'out/evaluation/speed10m-v45.request.csv'),
             '-out', str(ROOT/'out/evaluation/speed10m-v53.result.csv')], speedlog)
        text = speedlog.read_text()
        cpu = float(re.search(r'cpu_seconds=([\d.]+)', text)[1])
        init = float(re.search(r'initialization_seconds=([\d.]+)', text)[1])
        item = dict(chosen, cpp_evaluation=evaluation, reference_mismatch_rows=int(np.sum(diff > 0)),
                    reference_max_abs_difference_ps=int(diff.max()), speed10m_cpu_seconds=cpu,
                    estimated_billion_cpu_seconds=init+100*(cpu-init),
                    runtime_file_bytes=sum(p.stat().st_size for p in (binary, bounds, base_path, route_path)))
        report['candidates'].append(item)
        (ROOT/'reports/V53-cpu-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(item), flush=True)
    report['state'] = 'complete'
    (ROOT/'reports/V53-cpu-comparison.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
