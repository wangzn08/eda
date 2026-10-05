"""Export architecture-only spatial differences; verify complete core roundtrip."""
import hashlib
import json
import struct
import zlib
import numpy as np
from architecture import ROOT


def main():
    path = ROOT/'out/architecture-benchmark/periodic-dense.raw.bin'
    output = ROOT/'out/architecture-benchmark/core-template-zlib.bin'
    with path.open('rb') as f:
        assert f.read(8) == b'ANCHOR02'
        arch = f.read(64)
        ports = np.frombuffer(f.read(320), dtype='<u2').copy()
    source = np.memmap(path, dtype='<u2', mode='r', offset=392, shape=(160, 496, 59, 71))
    compressor = zlib.compressobj(6)
    expected = hashlib.sha256()
    with output.open('wb') as f:
        f.write(b'COREZL01'+arch+ports.tobytes()+struct.pack('<Q', 160*160*59*71*2))
        for row in range(160):
            core = np.asarray(source[row, ports], dtype=np.int32)
            expected.update(core.astype('<u2').tobytes())
            delta = core.copy()
            delta[:, 1:, :] -= core[:, :-1, :]
            delta[:, :, 1:] -= core[:, :, :-1]
            delta[:, 1:, 1:] += core[:, :-1, :-1]
            assert np.all((delta >= -32768) & (delta <= 32767))
            f.write(compressor.compress(delta.astype('<i2').tobytes()))
        f.write(compressor.flush())
    with output.open('rb') as f:
        header = f.read(400)
        compressed = f.read()
    assert header[:8] == b'COREZL01'
    inflater = zlib.decompressobj()
    raw = inflater.decompress(compressed)+inflater.flush()
    assert inflater.eof and not inflater.unused_data and len(raw) == 160*160*59*71*2
    differences = np.frombuffer(raw, dtype='<i2').reshape(160, 160, 59, 71)
    reconstructed_hash = hashlib.sha256()
    mismatch = 0
    for row in range(160):
        restored = differences[row].astype(np.int32).cumsum(axis=1, dtype=np.int32).cumsum(axis=2, dtype=np.int32)
        assert np.all((restored >= 0) & (restored <= 65535))
        mismatch += int(np.sum(restored != source[row, ports]))
        reconstructed_hash.update(restored.astype('<u2').tobytes())
    assert mismatch == 0 and expected.digest() == reconstructed_hash.digest()
    report = {'scope': 'Lossless finite-window architecture asset only; not request precision or runtime acceptance',
              'file': str(output.relative_to(ROOT)), 'bytes': output.stat().st_size,
              'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'decoded_core_bytes': len(raw), 'decoded_core_sha256': expected.hexdigest(),
              'core_values_compared': 160*160*59*71, 'roundtrip_mismatch_values': mismatch,
              'architecture_sha256': arch.decode(),
              'format': 'COREZL01, architecture hash64, ports160 uint16, decoded bytes uint64, zlib spatial int16 differences',
              'limitations': 'C++ decoder and inference still pending; zlib dependency availability in official environment unverified; no PDB can be added within 100MB'}
    (ROOT/'reports/core-template-export.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
