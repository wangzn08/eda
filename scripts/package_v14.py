"""Freeze a standalone V14 source/runtime bundle for acceptance."""
import hashlib,json,shutil,subprocess,tarfile,gzip
from pathlib import Path
from architecture import ROOT

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def remove_function(text,name):
    start=text.index('Distance '+name+'(');pos=text.index('{',start);depth=1;end=pos+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[:start]+text[end:]

def main():
    folder=ROOT/'out/acceptance-v14/bundle';folder.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/estimate.cpp').read_text()
    for version in (7,9,10):
        source=source.replace(f'#include "v{version}_tree_model.hpp"\n','')
        source=remove_function(source,f'v{version}_tree_delay')
        source=source.replace(f'|v{version}-tree','')
        source=source.replace(f' && algorithm!="v{version}-tree"','')
        source=source.replace(f' || algorithm=="v{version}-tree"','')
        source=source.replace(f'                algorithm=="v{version}-tree"?v{version}_tree_delay(from,to):\n','')
    source=source.replace('#include <fstream>','#include <fstream>\n#include <filesystem>')
    source=source.replace('algorithm="v6-pair"','algorithm="v14-tree"')
    source=source.replace('        if(input.empty()', '''        if(algorithm=="v14-tree") {
            auto directory=std::filesystem::weakly_canonical(std::filesystem::path(argv[0])).parent_path();
            if(oracle_path.empty()) oracle_path=(directory/"local-paths.bin").string();
            if(cycle_path.empty()) cycle_path=(directory/"long-tail.bin").string();
        }
        if(input.empty()''')
    (folder/'estimate.cpp').write_text(source)
    import re
    for name in re.findall(r'#include "([^"]+)"',source):
        shutil.copy2(ROOT/'src'/name,folder/name)
    # Transitive dependencies of the path components.
    for name in ('local_path_oracle.hpp','cycle_prefix_bank.hpp'):
        shutil.copy2(ROOT/'src'/name,folder/name)
    assets={'local-paths.bin':ROOT/'out/local-oracle/factorized-20-planes.bin',
            'long-tail.bin':ROOT/'out/local-oracle/long-tail-12-dict.bin'}
    for name,path in assets.items():shutil.copy2(path,folder/name)
    (folder/'README.md').write_text('''# V14 acceptance bundle

Build with a C++17 compiler:

    c++ -std=c++17 -O3 estimate.cpp -o estimate

Keep local-paths.bin and long-tail.bin beside the executable. Run:

    ./estimate -in requests.csv -out results.csv

The default is V14. The in-process cache stores only computed predictions;
--no-cache disables it. No golden file is needed or read at runtime.

This executable was built for macOS arm64. Rebuild from source for Linux or
another CPU. Local measurements do not certify the organizer's machine.
The bundle includes architecture-derived local path resources, not request
answers. The fixed model is trained on the development partition only.
''')
    subprocess.run(['c++','-std=c++17','-O3','-Wall','-Wextra','-Wpedantic',str(folder/'estimate.cpp'),'-o',str(folder/'estimate')],check=True)
    files={p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(folder.iterdir()) if p.is_file() and p.name!='manifest.json'}
    report={'candidate':'V14','model_frozen_sha256':digest(ROOT/'src/v14_tree_model.hpp'),
            'runtime_bytes':sum(files[n]['bytes'] for n in ('estimate','local-paths.bin','long-tail.bin')),
            'all_bundle_bytes':sum(v['bytes'] for v in files.values()),'files':files}
    (folder/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    archive=folder.parent/'fpga-delay-estimator-v14.tar.gz'
    def normalize(info):info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0;return info
    with archive.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as zipped:
        with tarfile.open(fileobj=zipped,mode='w') as tar:
            for p in sorted(folder.iterdir()):tar.add(p,arcname='fpga-delay-estimator-v14/'+p.name,filter=normalize)
    report.update(archive_bytes=archive.stat().st_size,archive_sha256=digest(archive),archive=str(archive),
                  archive_under_100mb=archive.stat().st_size<=100000000,runtime_under_100mb=report['runtime_bytes']<=100000000)
    (ROOT/'reports/V14-package-acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2),flush=True)

if __name__=='__main__':main()
