"""Reproducible small-scale correctness and resource check; never scores holdout."""
import csv
import hashlib
import json
import math
import platform
import re
import subprocess
import time
from pathlib import Path
from architecture import DEFAULT_ARCH, ROOT, Architecture
from audit_data import partition
from evaluate import metrics


def write_csv(path, fields, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)


def run(name, rows, algorithm, stats_enabled=True):
    directory = ROOT / 'out/baseline'
    directory.mkdir(parents=True, exist_ok=True)
    inp, out, stats = (directory / (name + ext) for ext in ('.request.csv', '.result.csv', '.stats.csv'))
    write_csv(inp, ['From', 'To'], rows)
    cmd = [str(ROOT/'build/estimate'), '-in', str(inp), '-out', str(out)]
    cmd += ['--algorithm', algorithm]
    if stats_enabled:
        cmd += ['--stats', str(stats)]
    # macOS time reports maximum resident set size in bytes.
    actual_cmd = ['/usr/bin/time', '-l'] + cmd if platform.system() == 'Darwin' else cmd
    started = time.perf_counter()
    process = subprocess.run(actual_cmd, capture_output=True, text=True, timeout=240, cwd=directory)
    elapsed = time.perf_counter() - started
    (directory/(name+'.log')).write_text(process.stderr)
    if process.returncode:
        raise RuntimeError(process.stderr)
    with out.open(newline='') as f:
        evaluated = metrics(rows, list(csv.DictReader(f)))
    timings = []
    if stats_enabled:
        with stats.open(newline='') as f:
            timings = sorted(float(r['wall_ms']) for r in csv.DictReader(f))
    match = re.search(r'(\d+)\s+maximum resident set size', process.stderr)
    cpu = re.search(r'([0-9.]+) user\s+([0-9.]+) sys', process.stderr)
    query = lambda p: timings[min(len(timings)-1, max(0,math.ceil(len(timings)*p)-1))] if timings else None
    evaluated.update({'name': name, 'algorithm': algorithm, 'wall_seconds': elapsed,
                      'cpu_user_plus_system_seconds_rounded': float(cpu.group(1))+float(cpu.group(2)) if cpu else None,
                      'peak_rss_bytes': int(match.group(1)) if match else None,
                      'query_wall_ms_min': query(0), 'query_wall_ms_max': query(1),
                      'query_wall_ms_median': query(.5),
                      'query_wall_ms_p95': query(.95),
                      'query_wall_ms_p99': query(.99),
                      'output_sha256': hashlib.sha256(out.read_bytes()).hexdigest(), 'command': cmd})
    print(json.dumps(evaluated, ensure_ascii=False), flush=True)
    assert evaluated['exact_matches'] == len(rows), name
    return evaluated


def main():
    data = DEFAULT_ARCH.parent/'data'
    with (data/'delay_estimate_check.csv').open(newline='') as f:
        checks = list(csv.DictReader(f))
    results = [run('official8_bidirectional', checks, 'bidirectional'), run('official8_dijkstra', checks, 'dijkstra')]
    assert results[0]['output_sha256'] == results[1]['output_sha256']
    a = Architecture()
    sampled, bucket_counts = [], {}
    with (data/'delay_estimate_ans.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            if partition(row['From'], row['To']) != 'development':
                continue
            (x,y), _, _ = a.pin(row['From'])
            (xx,yy), _, _ = a.pin(row['To'])
            distance=abs(x-xx)+abs(y-yy)
            bucket='0-15' if distance<16 else '16-63' if distance<64 else '64-255' if distance<256 else '256+'
            if bucket_counts.get(bucket,0)<2:
                sampled.append(row); bucket_counts[bucket]=bucket_counts.get(bucket,0)+1
            if len(sampled)==8:
                break
    assert len(sampled)==8
    zero={'From': checks[0]['From'], 'To': checks[0]['From'], 'delay':'0'}
    sampled.append(zero)
    # Reordered duplicate queries check reset logic and deterministic output.
    sampled += [sampled[1],sampled[0]]
    results.append(run('development8_zero_repeats', sampled, 'bidirectional'))
    repeated=run('official8_repeat', checks, 'bidirectional', stats_enabled=False)
    assert repeated['output_sha256']==results[0]['output_sha256']
    results.append(repeated)
    report={'machine': platform.platform(), 'processor': platform.machine(),
            'compiler': subprocess.check_output(['clang++','--version'],text=True).splitlines()[0],
            'build': 'make -j1; C++17 -O3',
            'files_sha256': {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/estimate.cpp','scripts/architecture.py','scripts/generate_architecture.py','src/architecture_data.hpp','build/estimate']},
            'selection': '8 official paths; 2 first development requests per Manhattan bucket; synthetic identical endpoint; reordered duplicates. No holdout scoring. Exact reference passes --algorithm explicitly because the default is the fast submission model.',
            'runs': results}
    (ROOT/'out/baseline/report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    main()
