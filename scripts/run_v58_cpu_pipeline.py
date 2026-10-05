"""Measure selected adaptive tree-prefix policies with full validation parity."""
import json
import re
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from run_v51_pipeline import run


def main():
    selected = json.loads((ROOT/'reports/V58-adaptive-trees-selection.json').read_text())
    folder = ROOT/'out/v58'
    folder.mkdir(exist_ok=True)
    python = str(ROOT/'out/research-env/bin/python')
    x, _, _, _ = load('validation')
    distance = x[:, 6]+x[:, 7]
    predictions = {n: np.load(ROOT/f'out/v56/correction-{n}.npy') for n in (128, 256, 512, 1024)}
    binary = ROOT/'build/core_template_estimate'
    core = ROOT/'out/architecture-benchmark/core-template-zlib.bin'
    model = ROOT/'out/v56/correction-1024.bin'
    report = {'state': 'running', 'holdout_used': False,
              'scope': 'Validation-selected compute allocation; billion timing extrapolated, not official acceptance',
              'candidates': []}
    for limit in (350, 400):
        candidate = max((c for c in selected['candidates'] if c['mean_trees'] <= limit), key=lambda c: c['score'])
        near, middle, far = candidate['near_distance'], candidate['middle_distance'], candidate['far_trees']
        name = f'n{near}-m{middle}-f{far}'
        reference = folder/f'{name}.npy'
        np.save(reference, np.where(distance < near, predictions[1024],
                                   np.where(distance < middle, predictions[512], predictions[far])))
        command = [str(binary), '--model', str(core), '--residual-model', str(model), '--trees', '1024',
                   '--adaptive-trees', '--near-distance', str(near), '--middle-distance', str(middle),
                   '--far-trees', str(far), '--no-cache']
        pred = ROOT/f'out/evaluation/validation.v58-{name}.csv'
        log = folder/f'{name}-validation.log'
        run(['/usr/bin/time', '-l', *command, '-in', str(ROOT/'out/evaluation/validation.request.csv'),
             '-out', str(pred)], log)
        run([python, 'scripts/evaluate_fast_phase.py', '--name', f'V58-{name}-cpp', '--prediction',
             str(pred.relative_to(ROOT)), '--log', str(log.relative_to(ROOT)),
             '--reference', str(reference.relative_to(ROOT))], folder/f'{name}-evaluation.log')
        evaluation = json.loads((ROOT/f'reports/V58-{name}-cpp.json').read_text())
        speedlog = folder/f'{name}-speed10m.log'
        run(['/usr/bin/time', '-l', *command, '-in', str(ROOT/'out/evaluation/speed10m-v45.request.csv'),
             '-out', str(ROOT/'out/evaluation/speed10m-v58.result.csv')], speedlog)
        text = speedlog.read_text()
        cpu = float(re.search(r'cpu_seconds=([\d.]+)', text)[1])
        init = float(re.search(r'initialization_seconds=([\d.]+)', text)[1])
        item = dict(candidate, cpp_evaluation=evaluation, speed10m_cpu_seconds=cpu,
                    estimated_billion_cpu_seconds=init+100*(cpu-init),
                    runtime_file_bytes=sum(p.stat().st_size for p in (binary, core, model)))
        report['candidates'].append(item)
        (ROOT/'reports/V58-cpu-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(item), flush=True)
    report['state'] = 'complete'
    (ROOT/'reports/V58-cpu-comparison.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
