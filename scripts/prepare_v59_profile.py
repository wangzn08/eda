"""Prepare an independent obstacle-aware research profile, not final acceptance."""
import hashlib
import json
import shutil
from architecture import ROOT


def main():
    folder = ROOT/'out/phase-fast-v59'
    folder.mkdir(exist_ok=True)
    files = {'estimate': ROOT/'build/core_template_estimate',
             'core-template.bin': ROOT/'out/architecture-benchmark/core-template-zlib.bin',
             'correction.bin': ROOT/'out/v59/correction-256.bin'}
    for name, path in files.items():
        shutil.copy2(path, folder/name)
    report = {'scope': 'Research profile; zlib runtime dependency; not official acceptance',
              'architecture': 'Architecture core template plus signed obstacle-period residual, 256 trees',
              'result_cache': False, 'validation_score': 97.88730718324194,
              'files': {name: {'bytes': (folder/name).stat().st_size,
                               'sha256': hashlib.sha256((folder/name).read_bytes()).hexdigest()}
                        for name in files}}
    report['runtime_file_bytes'] = sum(p['bytes'] for p in report['files'].values())
    (folder/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
