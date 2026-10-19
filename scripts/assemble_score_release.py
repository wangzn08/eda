"""Assemble a complete measured release using shared architecture assets."""
import argparse,hashlib,json,shutil,tarfile
from pathlib import Path
from architecture import ROOT

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--version',required=True,type=int);p.add_argument('--output',required=True);p.add_argument('--overwrite',action='store_true');p.add_argument('--archive',action='store_true');a=p.parse_args()
release=ROOT/f'artifacts/runtime-v{a.version}';common=ROOT/'artifacts/runtime-v219';destination=Path(a.output)
if not destination.is_absolute():destination=ROOT/destination
manifest=json.loads((release/'BUILD_MANIFEST.json').read_text())
files={**manifest['runtime_asset_sha256'],**manifest['source_sha256']}
extras=release/'SNAPSHOT_EXTRAS.json'
if extras.exists():files.update(json.loads(extras.read_text()))
for name,expected in files.items():
 source=release/name
 if not source.exists():source=common/name
 assert source.is_file() and digest(source)==expected,source
 target=destination/name
 if target.exists() and digest(target)!=expected and not a.overwrite:raise RuntimeError(f'Existing different file: {target}')
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 assert digest(target)==expected
target=destination/'BUILD_MANIFEST.json'
if target.exists() and digest(target)!=digest(release/'BUILD_MANIFEST.json') and not a.overwrite:raise RuntimeError(f'Existing different manifest: {target}')
shutil.copy2(release/'BUILD_MANIFEST.json',target)
size=sum(p.stat().st_size for p in destination.rglob('*') if p.is_file());assert size<=100000000
result={'version':a.version,'directory':str(destination),'bytes':size,'runtime_and_source_sha256_verified':True}
if a.archive:
 archive=destination.parent/f'fpga-delay-v{a.version}.tar.gz'
 with tarfile.open(archive,'w:gz') as tar:tar.add(destination,arcname=destination.name)
 result.update(archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=digest(archive))
print(json.dumps(result,indent=2))
