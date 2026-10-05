"""Prepare a local research profile; not a final submission acceptance package."""
import hashlib
import json
import shutil
from architecture import ROOT


def main():
    folder = ROOT/'out/phase-fast-v53'
    folder.mkdir(exist_ok=True)
    files = {'estimate': ROOT/'build/phase_fast_estimate',
             'phase-bounds.bin': ROOT/'models/phase-bounds-safe.bin',
             'residual.bin': ROOT/'models/fast-residual-v50.bin',
             'route.bin': ROOT/'out/v51/h64-r64.bin'}
    for name, path in files.items():
        shutil.copy2(path, folder/name)
    report = {'scope': 'Local research profile, not official acceptance',
              'architecture': 'V50 residual trees for distance below 150; V51 64-width 64-route model otherwise',
              'result_cache': False, 'route_min_distance': 150,
              'files': {name: {'bytes': (folder/name).stat().st_size,
                               'sha256': hashlib.sha256((folder/name).read_bytes()).hexdigest()}
                        for name in files}}
    report['runtime_file_bytes'] = sum(item['bytes'] for item in report['files'].values())
    (folder/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    (folder/'README.md').write_text('Research V53 profile. Run: ./estimate -in requests.csv -out results.csv\n'
                                  'No result cache by default. Validation 97.1350; billion timing is extrapolated.\n'
                                  'Not a certified precision model or official submission acceptance.\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
