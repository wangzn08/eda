"""Train signed core-template corrections, then export and measure serially."""
import argparse
import csv
import json
import os
import re
import time
import numpy as np
from catboost import CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features
from experiment_v7_teacher import score
from run_v51_pipeline import run


def delays(path):
    with path.open() as f:
        return np.array([int(row['delay']) for row in csv.DictReader(f)], dtype=np.float32)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', type=int, required=True)
    args = p.parse_args()
    waiting = ROOT/'reports/V54-cpu-comparison.json'
    while not waiting.exists() or json.loads(waiting.read_text()).get('state') != 'complete':
        try:
            os.kill(args.wait_pid, 0)
        except ProcessLookupError:
            raise RuntimeError('V54 pipeline ended without completion')
        time.sleep(30)
    python = str(ROOT/'out/research-env/bin/python')
    folder = ROOT/'out/v56'
    folder.mkdir(exist_ok=True)
    x, y, _, _ = load('development')
    xv, yv, _, _ = load('validation')
    base = delays(ROOT/'out/evaluation/development.v47-directional.csv')
    bv = delays(ROOT/'out/evaluation/validation.v55-core.csv')
    assert len(base) == len(y)
    a, av = features(x, base), features(xv, bv)
    m = y > 0
    model = CatBoostRegressor(iterations=1024, depth=10, learning_rate=.07,
                             loss_function='MAE', thread_count=2, random_seed=20261009,
                             l2_leaf_reg=5, verbose=128, allow_writing_files=False)
    model.fit(a[m], (y[m]-base[m])/100, sample_weight=1/np.maximum(y[m], 1))
    source = folder/'correction.json'
    model.save_model(str(source), format='json')
    binary = ROOT/'build/core_template_estimate'
    core = ROOT/'out/architecture-benchmark/core-template-zlib.bin'
    report = {'state': 'running', 'fit_split': 'development', 'holdout_used': False,
              'baseline_score': score(yv, bv),
              'scope': 'Signed correction of architecture templates; no PDB asset, no path certificate; billion estimated',
              'candidates': []}
    for trees in (64, 128, 256, 512, 1024):
        pred = np.rint(np.maximum(0, bv+100*model.predict(av, ntree_end=trees, thread_count=2)))
        name = f'correction-{trees}'
        reference = folder/f'{name}.npy'
        np.save(reference, pred)
        asset = folder/f'{name}.bin'
        run([python, 'scripts/export_fast_residual.py', str(source), str(asset), '--trees', str(trees)],
            folder/f'{name}-export.log')
        bytes_total = sum(p.stat().st_size for p in (binary, core, asset))
        item = {'trees': trees, 'python_validation_score': score(yv, pred), 'runtime_file_bytes': bytes_total}
        if bytes_total > 100000000:
            item['rejected'] = 'Runtime assets exceed 100MB; not measured'
        else:
            command = [str(binary), '--model', str(core), '--residual-model', str(asset),
                       '--trees', str(trees), '--no-cache']
            output = ROOT/f'out/evaluation/validation.v56-{name}.csv'
            log = folder/f'{name}-validation.log'
            run(['/usr/bin/time', '-l', *command, '-in', str(ROOT/'out/evaluation/validation.request.csv'),
                 '-out', str(output)], log)
            run([python, 'scripts/evaluate_fast_phase.py', '--name', f'V56-{name}-cpp',
                 '--prediction', str(output.relative_to(ROOT)), '--log', str(log.relative_to(ROOT)),
                 '--reference', str(reference.relative_to(ROOT))], folder/f'{name}-evaluation.log')
            item['cpp_evaluation'] = json.loads((ROOT/f'reports/V56-{name}-cpp.json').read_text())
            speedlog = folder/f'{name}-speed10m.log'
            run(['/usr/bin/time', '-l', *command, '-in', str(ROOT/'out/evaluation/speed10m-v45.request.csv'),
                 '-out', str(ROOT/'out/evaluation/speed10m-v56.result.csv')], speedlog)
            text = speedlog.read_text()
            cpu = float(re.search(r'cpu_seconds=([\d.]+)', text)[1])
            init = float(re.search(r'initialization_seconds=([\d.]+)', text)[1])
            item.update(speed10m_cpu_seconds=cpu, estimated_billion_cpu_seconds=init+100*(cpu-init))
        report['candidates'].append(item)
        (ROOT/'reports/V56-template-correction.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(item), flush=True)
    report['state'] = 'complete'
    (ROOT/'reports/V56-template-correction.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
