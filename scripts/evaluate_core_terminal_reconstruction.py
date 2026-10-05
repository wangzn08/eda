"""Evaluate architecture-only terminal factorization over the entire template."""
import json
import numpy as np
from architecture import Architecture, ROOT


def main():
    arch = Architecture()
    path = ROOT/'out/architecture-benchmark/periodic-dense.raw.bin'
    with path.open('rb') as f:
        assert f.read(8) == b'ANCHOR02'
        arch_hash = f.read(64).decode()
        ports = np.frombuffer(f.read(320), dtype='<u2').copy()
    index = {int(port): i for i, port in enumerate(ports)}
    incoming = []
    for arc in arch.arcs:
        source, target = arch.port_ids[arc['from']], arch.port_ids[arc['to']]
        if source in index:
            incoming.append((index[source], target, arc['delay']))
    values = np.memmap(path, dtype='<u2', mode='r', offset=392, shape=(160, 496, 59, 71))
    mismatch, max_diff, examples = 0, 0, []
    for source in range(160):
        core = np.asarray(values[source, ports], dtype=np.int32)
        reconstructed = np.full((496, 59, 71), 65535, dtype=np.int32)
        reconstructed[ports] = core
        for node, target, cost in incoming:
            np.minimum(reconstructed[target], core[node]+cost, out=reconstructed[target])
        reference = np.asarray(values[source], dtype=np.int32)
        delta = np.abs(reference-reconstructed)
        mismatch += int(np.sum(delta != 0))
        max_diff = max(max_diff, int(delta.max()))
        if np.any(delta) and len(examples) < 5:
            target, ix, iy = np.argwhere(delta != 0)[0]
            examples.append({'source_index': source, 'target_port': int(target),
                             'dx': int(ix)-29, 'dy': int(iy)-35,
                             'reference': int(reference[target, ix, iy]),
                             'reconstructed': int(reconstructed[target, ix, iy])})
    report = {'scope': 'Exact factorization of the finite architecture-only template; not hidden request precision',
              'arch_sha256': arch_hash, 'values_compared': 160*496*59*71,
              'mismatch_values': mismatch, 'max_abs_difference_ps': max_diff,
              'examples': examples, 'source_data': str(path.relative_to(ROOT)),
              'formula': 'min(core target distance, incoming local arc delay + corresponding core distance)'}
    (ROOT/'reports/core-terminal-reconstruction.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
