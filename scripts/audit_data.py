"""Read official data, replay paths and record deterministic sample partitions."""
import collections
import csv
import hashlib
import json
from pathlib import Path
from architecture import Architecture, DEFAULT_ARCH, ROOT


def partition(source, target):
    digest = hashlib.blake2b((source + '\0' + target).encode(), digest_size=8).digest()
    value = int.from_bytes(digest, 'little') % 100
    return 'development' if value < 70 else 'validation' if value < 85 else 'holdout'


def main():
    a = Architecture()
    assert len(a.sites) == len(a.instances) == len(a.coordinates)
    assert len(a.port_ids) == len(a.ports)
    assert len({b['id'] for b in a.blocks}) == len(a.blocks)
    block_cells = set()
    for b in a.blocks:
        cells = {(x, y) for x in range(b['left'], b['right'] + 1) for y in range(b['lower'], b['upper'] + 1)}
        assert not cells & block_cells, 'Overlapping Blocks require an explicit rule'
        block_cells.update(cells)
    missing = {(x, y) for x in range(a.width) for y in range(a.height)} - a.sites.keys()
    assert missing == block_cells, 'Inst omissions do not match Blocks'
    for item in a.arcs + a.nets:
        assert item['from'] in a.port_ids and item['to'] in a.port_ids
        assert isinstance(item.get('delay', 0), int) and item.get('delay', 0) >= 0
    for n in a.nets:
        assert bool(n['delta x']) != bool(n['delta y'])
    for item in a.lines:
        assert item['delay'] >= 0
    data = DEFAULT_ARCH.parent / 'data'
    report = {'schema_version': 1, 'files': {}, 'architecture': {
        'width': a.width, 'height': a.height, 'instances': len(a.instances),
        'ports': len(a.ports), 'arcs': len(a.arcs), 'net_templates': len(a.nets),
        'line_gaps': len(a.lines), 'block_gaps': len(a.blocks), 'absent_sites': len(missing),
        'implicit_nodes': len(a.instances) * len(a.ports),
        'expanded_internal_edges': len(a.instances) * len(a.arcs),
        'arc_delay_min': min(x['delay'] for x in a.arcs),
        'arc_delay_max': max(x['delay'] for x in a.arcs),
        'net_vectors': sorted({(n['delta x'], n['delta y']) for n in a.nets}),
        'net_base_delay': 'absent in official JSON; interpreted as zero',
    }, 'path_replays': []}
    for p in sorted(list(DEFAULT_ARCH.glob('*.json')) + list(data.glob('*.csv'))):
        report['files'][str(p.relative_to(ROOT))] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    with (data / 'delay_estimate_check.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            path = [p.strip() for p in row['Path'].split('|')]
            assert path[0] == row['From'] and path[-1] == row['To']
            edges = [a.edge_delay(s, t) for s, t in zip(path, path[1:])]
            assert sum(edges) == int(row['Min Delay']), (row['From'], sum(edges), row['Min Delay'])
            report['path_replays'].append({'from': row['From'], 'to': row['To'], 'golden': int(row['Min Delay']), 'sum': sum(edges), 'edges': len(edges)})
    pairs, sources, targets = {}, set(), set()
    partitions, source_types, target_types, distances = (collections.Counter() for _ in range(4))
    split_unique = collections.Counter()
    total, minimum, maximum, zeros = 0, None, 0, 0
    with (data / 'delay_estimate_ans.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            s, t = row['From'].strip(), row['To'].strip()
            (x, y), sp, si = a.pin(s)
            (xx, yy), tp, ti = a.pin(t)
            golden = int(row['delay'])
            assert golden >= 0
            key = (si << 32) | ti
            if key in pairs:
                assert pairs[key] == golden, 'Conflicting labels for repeated pair'
            else:
                pairs[key] = golden
                split_unique[partition(s, t)] += 1
            sources.add(si); targets.add(ti)
            partitions[partition(s, t)] += 1
            source_types['INTER' if sp[0] in 'IZ' else 'LOGIC'] += 1
            target_types['INTER' if tp[0] in 'IZ' else 'LOGIC'] += 1
            distance = abs(x - xx) + abs(y - yy)
            distances['0-15' if distance < 16 else '16-63' if distance < 64 else '64-255' if distance < 256 else '256+'] += 1
            total += 1
            minimum = golden if minimum is None else min(minimum, golden)
            maximum = max(maximum, golden)
            zeros += golden == 0
    report['public_samples'] = {
        'rows': total, 'unique_pairs': len(pairs), 'duplicate_rows': total-len(pairs),
        'unique_sources': len(sources), 'unique_targets': len(targets),
        'golden_min': minimum, 'golden_max': maximum, 'zero_golden': zeros,
        'split_rows': dict(partitions), 'split_unique_pairs': dict(split_unique),
        'source_types': dict(source_types), 'target_types': dict(target_types),
        'manhattan_distance_histogram': dict(distances),
    }
    report['scope'] = 'Path replay validates legal edges and sums; it does not independently prove shortest distances. No held-out prediction scores are computed.'
    out = ROOT / 'out'
    out.mkdir(exist_ok=True)
    (out / 'data_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
