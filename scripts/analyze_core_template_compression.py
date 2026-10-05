"""Architecture-only lossless core template storage analysis; no labels."""
import json
import math
import zlib
import numpy as np
from architecture import ROOT


def main():
    path = ROOT/'out/architecture-benchmark/periodic-dense.raw.bin'
    with path.open('rb') as f:
        magic, arch = f.read(8), f.read(64).decode()
        ports = np.frombuffer(f.read(320), dtype='<u2').copy()
    assert magic == b'ANCHOR02' and len(set(ports)) == 160
    values = np.memmap(path, dtype='<u2', mode='r', offset=392, shape=(160, 496, 59, 71))
    dx = np.arange(-29, 30)[:, None]
    dy = np.arange(-35, 36)[None, :]
    plane = np.floor(12.5*np.abs(dx) + np.where(dy > 0, 127/12, 125/12)*np.abs(dy)).astype(np.int32)
    bits, unreachable, pair_bytes = [], 0, []
    tiled = {size: {'payload_bytes': 0, 'blocks': 0, 'max_bit_width': 0} for size in (4, 8, 16)}
    compressed = {'raw_core_zlib1_pair_bytes': 0, 'delta2d_zlib1_pair_bytes': 0,
                  'delta2d_zlib6_pair_bytes': 0}
    canonical_patterns = {}
    # Original targets include local output terminals; retain only the 160 net-arrival cores.
    for source in range(160):
        core = np.asarray(values[source, ports], dtype=np.int32)
        unreachable += int(np.sum(core == 65535))
        residual = core - plane
        delta = core.copy()
        delta[:, 1:, :] -= core[:, :-1, :]
        delta[:, :, 1:] -= core[:, :, :-1]
        delta[:, 1:, 1:] += core[:, :-1, :-1]
        assert np.all((delta >= -32768) & (delta <= 32767))
        for pair, changes in zip(core, delta):
            compressed['raw_core_zlib1_pair_bytes'] += len(zlib.compress(pair.astype('<u2').tobytes(), 1))
            compressed['delta2d_zlib1_pair_bytes'] += len(zlib.compress(changes.astype('<i2').tobytes(), 1))
            compressed['delta2d_zlib6_pair_bytes'] += len(zlib.compress(changes.astype('<i2').tobytes(), 6))
            canonical = changes.astype('<i2')
            canonical[0, 0] = 0
            pattern = canonical.tobytes()
            if pattern not in canonical_patterns:
                canonical_patterns[pattern] = len(zlib.compress(pattern, 6))
        span = residual.max((1, 2))-residual.min((1, 2))
        widths = [int(v).bit_length() for v in span]
        bits.extend(widths)
        pair_bytes.extend((4189*b+7)//8 for b in widths)
        for size, item in tiled.items():
            for ix in range(0, 59, size):
                for iy in range(0, 71, size):
                    tile = residual[:, ix:ix+size, iy:iy+size]
                    span = tile.max((1, 2))-tile.min((1, 2))
                    width = np.ceil(np.log2(span.astype(np.float64)+1)).astype(np.int64)
                    item['payload_bytes'] += int(np.sum((tile.shape[1]*tile.shape[2]*width+7)//8))
                    item['blocks'] += len(width)
                    item['max_bit_width'] = max(item['max_bit_width'], int(width.max()))
    for item in tiled.values():
        # Per tile: signed int16 baseline, uint8 width, uint32 byte offset.
        item['estimated_file_bytes'] = item['payload_bytes']+7*item['blocks']+392
    report = {'scope': 'Architecture-only finite-window exact storage; extrapolated distances remain approximate',
              'source': str(path.relative_to(ROOT)), 'arch_sha256': arch,
              'source_core_ports': 160, 'target_core_ports': 160,
              'original_bytes': path.stat().st_size, 'core_raw_bytes': 160*160*4189*2+392,
              'unreachable_core_values': unreachable,
              'residual_plane': 'floor(12.5*abs(dx)+(127/12 if dy>0 else 125/12)*abs(dy))',
              'per_pair_bit_width_histogram': {str(b): bits.count(b) for b in sorted(set(bits))},
              'estimated_packed_core_bytes': sum(pair_bytes)+160*160*16+392,
              'mean_bit_width': float(np.mean(bits)),
              'tiled_residual_storage': tiled,
              'pairwise_zlib_payload_bytes': compressed,
              'pairwise_zlib_index_bytes': 160*160*8+392,
              'constant_offset_dictionary': {
                  'unique_patterns': len(canonical_patterns),
                  'zlib6_payload_bytes': sum(canonical_patterns.values()),
                  'estimated_file_bytes': sum(canonical_patterns.values())+len(canonical_patterns)*8+160*160*6+392},
              'limitations': 'Destination local-arc reconstruction must be verified before replacing the original model; compression alone does not raise accuracy'}
    (ROOT/'reports/core-template-compression-analysis.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
