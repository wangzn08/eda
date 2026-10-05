"""Export distance experts, check full validation parity, measure 10m rows."""
import argparse
import hashlib
import json
import os
import re
import time
from architecture import ROOT
from run_v51_pipeline import run


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', type=int, required=True)
    args = p.parse_args()
    training_path = ROOT/'reports/V52-distance-specialist.json'
    while True:
        if training_path.exists():
            training = json.loads(training_path.read_text())
            if training.get('state') == 'complete':
                break
        try:
            os.kill(args.wait_pid, 0)
        except ProcessLookupError:
            raise RuntimeError('V52 training ended without completed report')
        time.sleep(30)
    python = str(ROOT/'out/research-env/bin/python')
    folder = ROOT/'out/v52'
    binary = ROOT/'build/phase_fast_estimate'
    base = ROOT/'models/fast-residual-v50.bin'
    bounds = ROOT/'models/phase-bounds-safe.bin'
    report = {'state': 'running', 'holdout_used': False,
              'scope': 'Validation-selected distance experts; 10m measured, billion estimated; no official acceptance',
              'candidates': []}
    for ceiling in (50, 100, 200):
        chosen = max((c for c in training['candidates'] if c['ceiling'] == ceiling),
                     key=lambda c: c['score'])
        trees = chosen['trees']
        name = f'distance-{ceiling}-{trees}'
        model = folder/f'{name}.bin'
        run([python, 'scripts/export_fast_residual.py', str(folder/f'distance-{ceiling}.json'),
             str(model), '--trees', str(trees)], folder/f'{name}-export.log')
        common = [str(binary), '--phase-bounds', str(bounds), '--residual-model', str(base),
                  '--trees', '256', '--distance-model', str(model), '--distance-trees', str(trees),
                  '--distance-limit', str(ceiling), '--no-cache']
        pred = ROOT/f'out/evaluation/validation.v52-{name}.csv'
        log = folder/f'{name}-validation.log'
        run(['/usr/bin/time', '-l', *common, '-in', str(ROOT/'out/evaluation/validation.request.csv'),
             '-out', str(pred)], log)
        run([python, 'scripts/evaluate_fast_phase.py', '--name', f'V52-{name}-cpp',
             '--prediction', str(pred.relative_to(ROOT)), '--log', str(log.relative_to(ROOT)),
             '--reference', str((folder/f'{name}.npy').relative_to(ROOT))], folder/f'{name}-evaluation.log')
        evaluation = json.loads((ROOT/f'reports/V52-{name}-cpp.json').read_text())
        speedlog = folder/f'{name}-speed10m.log'
        run(['/usr/bin/time', '-l', *common, '-in', str(ROOT/'out/evaluation/speed10m-v45.request.csv'),
             '-out', str(ROOT/'out/evaluation/speed10m-v52.result.csv')], speedlog)
        text = speedlog.read_text()
        cpu = float(re.search(r'cpu_seconds=([\d.]+)', text)[1])
        init = float(re.search(r'initialization_seconds=([\d.]+)', text)[1])
        item = dict(chosen, cpp_evaluation=evaluation, speed10m_cpu_seconds=cpu,
                    estimated_billion_cpu_seconds=init+100*(cpu-init),
                    estimate_formula='initialization + 100 * (measured_10m_cpu - initialization)',
                    runtime_file_bytes=sum(p.stat().st_size for p in (binary, base, bounds, model)),
                    model_sha256=hashlib.sha256(model.read_bytes()).hexdigest())
        report['candidates'].append(item)
        (ROOT/'reports/V52-cpu-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(item), flush=True)
    report['state'] = 'complete'
    (ROOT/'reports/V52-cpu-comparison.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
