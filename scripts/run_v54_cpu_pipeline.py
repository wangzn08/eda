"""Export joint phases and measure distance mixtures after training ends."""
import argparse
import csv
import hashlib
import json
import os
import re
import time
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from run_v51_pipeline import run


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', type=int, required=True)
    args = p.parse_args()
    path = ROOT/'reports/V54-joint-routes.json'
    while True:
        if path.exists():
            training = json.loads(path.read_text())
            if training.get('state') == 'complete':
                break
        try:
            os.kill(args.wait_pid, 0)
        except ProcessLookupError:
            raise RuntimeError('Joint training ended without completion; inspect log')
        time.sleep(30)
    folder, python = ROOT/'out/v54', str(ROOT/'out/research-env/bin/python')
    x, _, _, _ = load('validation')
    far = x[:, 6]+x[:, 7] >= 150
    base_prediction = np.load(ROOT/'out/v50/validation-10-256.npy')
    binary, bounds = ROOT/'build/phase_fast_estimate', ROOT/'models/phase-bounds-safe.bin'
    residual = ROOT/'models/fast-residual-v50.bin'
    report = {'state': 'running', 'holdout_used': False,
              'scope': 'Joint-phase factors trained with continuous official-score loss; fixed validation selection; billion estimate only',
              'candidates': []}
    for h, r in ((32, 128), (32, 256), (64, 256)):
        chosen = max((c for c in training['candidates'] if c['hidden'] == h and c['routes'] == r),
                     key=lambda c: c['distance150_mixed_score'])
        name = f'h{h}-r{r}'
        model = folder/f'{name}-factor.bin'
        run([python, 'scripts/export_tiny_routes.py', str(ROOT/chosen['weights']), str(model),
             '--phase-format', 'factor'], folder/f'{name}-export.log')
        command = [str(binary), '--phase-bounds', str(bounds), '--residual-model', str(residual),
                   '--trees', '256', '--route-model', str(model), '--route-min-distance', '150', '--no-cache']
        pred = ROOT/f'out/evaluation/validation.v54-{name}.csv'
        log = folder/f'{name}-validation.log'
        run(['/usr/bin/time', '-l', *command, '-in', str(ROOT/'out/evaluation/validation.request.csv'),
             '-out', str(pred)], log)
        run([python, 'scripts/evaluate_fast_phase.py', '--name', f'V54-{name}-cpp',
             '--prediction', str(pred.relative_to(ROOT)), '--log', str(log.relative_to(ROOT))],
            folder/f'{name}-evaluation.log')
        evaluation = json.loads((ROOT/f'reports/V54-{name}-cpp.json').read_text())
        reference = np.where(far, np.load(ROOT/chosen['weights'].replace('.pt', '.npy')), base_prediction)
        with pred.open() as f:
            cpp = np.array([int(row['delay']) for row in csv.DictReader(f)])
        diff = np.abs(cpp-reference)
        assert diff.max() <= 1, 'Joint export/CPU differs by more than 1ps'
        speedlog = folder/f'{name}-speed10m.log'
        run(['/usr/bin/time', '-l', *command, '-in', str(ROOT/'out/evaluation/speed10m-v45.request.csv'),
             '-out', str(ROOT/'out/evaluation/speed10m-v54.result.csv')], speedlog)
        text = speedlog.read_text()
        cpu = float(re.search(r'cpu_seconds=([\d.]+)', text)[1])
        init = float(re.search(r'initialization_seconds=([\d.]+)', text)[1])
        item = dict(chosen, cpp_evaluation=evaluation, reference_mismatch_rows=int(np.sum(diff > 0)),
                    reference_max_abs_difference_ps=int(diff.max()), speed10m_cpu_seconds=cpu,
                    estimated_billion_cpu_seconds=init+100*(cpu-init),
                    estimate_formula='initialization + 100*(measured_10m_cpu - initialization)',
                    runtime_file_bytes=sum(p.stat().st_size for p in (binary, bounds, residual, model)),
                    model_sha256=hashlib.sha256(model.read_bytes()).hexdigest())
        report['candidates'].append(item)
        (ROOT/'reports/V54-cpu-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(item), flush=True)
    report['state'] = 'complete'
    (ROOT/'reports/V54-cpu-comparison.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
