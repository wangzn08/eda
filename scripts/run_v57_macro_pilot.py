"""Compare real-path macro shortcuts on a fixed 1001-row validation pilot."""
import argparse
import csv
import json
import os
import time
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score
from run_v51_pipeline import run


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', type=int, required=True)
    args = p.parse_args()
    waiting = ROOT/'reports/V56-template-correction.json'
    while not waiting.exists() or json.loads(waiting.read_text()).get('state') != 'complete':
        try:
            os.kill(args.wait_pid, 0)
        except ProcessLookupError:
            raise RuntimeError('Template correction pipeline ended without completion')
        time.sleep(30)
    golden = rows(ROOT/'out/evaluation/v57-pilot.golden.csv')
    y = np.array([int(row['delay']) for row in golden], dtype=np.float64)
    report = {'scope': 'First 1001 validation rows only; external V18 architecture-path incumbent initialization is not timed here; no billion throughput claim',
              'incumbent': 'out/evaluation/v57-pilot.bound.csv', 'holdout_used': False, 'candidates': []}
    for name, budget, weight, jumps in [('base32', 32, 1, False), ('jump32', 32, 1, True),
                                       ('jump8-w105', 8, 1.05, True), ('jump32-w105', 32, 1.05, True),
                                       ('jump128-w105', 128, 1.05, True)]:
        output = ROOT/f'out/evaluation/validation.v57-pilot-{name}.csv'
        log = ROOT/f'out/v57-{name}.log'
        command = [str(ROOT/'build/macro_oracle_apply'), str(ROOT/'out/evaluation/v57-pilot.bound.csv'),
                   str(output), str(ROOT/'out/phase-precision-v40/long-tail.bin'), str(budget),
                   '--gap-heuristic', '--phase-bounds', str(ROOT/'models/phase-bounds-safe.bin'),
                   '--priority-weight', str(weight)]
        if jumps:
            command.append('--repeat-jumps')
        run(['/usr/bin/time', '-l', *command], log)
        prediction = rows(output)
        assert len(prediction) == len(golden)
        assert all((a['From'], a['To']) == (b['From'], b['To']) for a, b in zip(golden, prediction))
        z = np.array([int(row['delay']) for row in prediction], dtype=np.float64)
        covered = z < 100000000
        under = int(np.sum(z[covered] < y[covered]))
        assert under == 0, 'Claimed feasible path cost below golden; inspect witnesses'
        item = {'name': name, 'budget': budget, 'priority_weight': weight, 'repeat_jumps': jumps,
                'rows': len(y), 'covered': int(covered.sum()), 'under_golden': under,
                'score_with_missing_zero_credit': score(y, z), 'score_covered': score(y[covered], z[covered]),
                'log': log.read_text()}
        report['candidates'].append(item)
        (ROOT/'reports/V57-weighted-macro-pilot.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(item), flush=True)
    report['state'] = 'complete'
    (ROOT/'reports/V57-weighted-macro-pilot.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
