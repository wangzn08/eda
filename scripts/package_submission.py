"""Build a self-contained C++17 source archive without official data files."""
import hashlib
import gzip
import json
import tarfile
from pathlib import Path

from architecture import ROOT


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output=ROOT/'out/submission'
    output.mkdir(parents=True,exist_ok=True)
    sources={
        'estimate.cpp':ROOT/'src/estimate.cpp',
        'architecture_data.hpp':ROOT/'src/architecture_data.hpp',
        'lookup_model.hpp':ROOT/'src/lookup_model.hpp',
        'spatial_model.hpp':ROOT/'src/spatial_model.hpp',
        'port_model.hpp':ROOT/'src/port_model.hpp',
        'source_x_model.hpp':ROOT/'src/source_x_model.hpp',
        'target_x_model.hpp':ROOT/'src/target_x_model.hpp',
        'dx_model.hpp':ROOT/'src/dx_model.hpp',
    }
    readme='''# FPGA delay estimator submission source

Build on the target machine with a C++17 compiler:

    c++ -std=c++17 -O3 estimate.cpp -o estimate

Run with the official two-column request CSV:

    ./estimate -in delay_estimate_request.csv -out delay_estimate_result.csv

The default uses the architecture-aware lookup model. The architecture and
fitted parameters are embedded in the supplied headers. No JSON or golden
answer file is read at runtime. Use --algorithm bidirectional for the slow
exact reference if needed for diagnostics.

The source was validated on macOS arm64. Rebuild and benchmark on the actual
contest machine; the organizer's target compiler, OS and packaging rules
must take precedence over this local package.
'''
    archive=output/'fpga-delay-estimator-v2-source.tar.gz'
    readme_path=output/'README.txt'
    readme_path.write_text(readme)
    def normalize(info):
        info.uid=info.gid=0
        info.uname=info.gname=''
        info.mtime=0
        return info
    with archive.open('wb') as raw, gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as zipped:
        with tarfile.open(fileobj=zipped,mode='w') as tar:
            for name,path in sources.items():
                tar.add(path,arcname=f'fpga-delay-estimator/{name}',filter=normalize)
            tar.add(readme_path,arcname='fpga-delay-estimator/README.txt',filter=normalize)
    report={'archive':str(archive),'archive_bytes':archive.stat().st_size,
            'archive_sha256':sha256(archive),
            'sources':{name:{'bytes':path.stat().st_size,'sha256':sha256(path)}
                       for name,path in sources.items()}}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
