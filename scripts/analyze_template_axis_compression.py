"""Lossless core-template difference transforms across spatial and port axes."""
import json
import zlib
import numpy as np
from architecture import ROOT


def main():
    path = ROOT/'out/architecture-benchmark/periodic-dense.raw.bin'
    with path.open('rb') as f:
        assert f.read(8) == b'ANCHOR02'
        arch = f.read(64).decode()
        ports = np.frombuffer(f.read(320), dtype='<u2').copy()
    values = np.memmap(path, dtype='<u2', mode='r', offset=392, shape=(160, 496, 59, 71))
    names = ('spatial2d', 'spatial2d_target', 'spatial2d_target_source')
    encoders = {name: zlib.compressobj(6) for name in names}
    sizes = {name: 0 for name in names}
    previous = None
    ranges = {name: [0, 0] for name in names}
    for source in range(160):
        core = np.asarray(values[source, ports], dtype=np.int32)
        spatial = core.copy()
        spatial[:, 1:, :] -= core[:, :-1, :]
        spatial[:, :, 1:] -= core[:, :, :-1]
        spatial[:, 1:, 1:] += core[:, :-1, :-1]
        target = spatial.copy()
        target[1:] -= spatial[:-1]
        both = target if previous is None else target-previous
        for name, data in zip(names, (spatial, target, both)):
            minimum, maximum = int(data.min()), int(data.max())
            assert -32768 <= minimum <= maximum <= 32767
            ranges[name][0] = min(ranges[name][0], minimum)
            ranges[name][1] = max(ranges[name][1], maximum)
            sizes[name] += len(encoders[name].compress(data.astype('<i2').tobytes()))
        previous = target
    for name in names:
        sizes[name] += len(encoders[name].flush())
    report = {'scope': 'Architecture-only lossless storage analysis; no labels, no accuracy claim',
              'arch_sha256': arch, 'core_shape': [160, 160, 59, 71],
              'codec': 'zlib level6 streaming whole core tensor',
              'payload_bytes': sizes, 'transformed_value_ranges': ranges,
              'estimated_asset_bytes': {name: size+392 for name, size in sizes.items()},
              'limitations': 'Must implement inverse cumulative transforms and verify exact reconstruction; target local-arc reconstruction remains unverified; no submitted asset yet'}
    (ROOT/'reports/template-axis-compression-analysis.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
