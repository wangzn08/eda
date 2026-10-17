"""Freeze default8-source profile; no serialized indices or request-result cache."""
import hashlib,json,shutil,subprocess
from pathlib import Path
from architecture import ROOT
out=ROOT/'out/phase-fast15-v112';out.mkdir(exist_ok=True)
flags=['-std=c++17','-O3','-flto','-mcpu=apple-m4','-ffp-contract=off','-DCORE_PHASE_MAJOR=1','-DCORE_FAST30_PROFILE=1','-DCORE_FAST15_PROFILE=1','-DCORE_BUFFERED_INPUT=1','-DCORE_PREFETCH=1','-DCORE_PREFETCH_CELL=1']
subprocess.run(['c++',*flags,'-Isrc','src/core_template_estimate.cpp',*[str(p.relative_to(ROOT)) for p in sorted((ROOT/'build/xz').glob('*.o'))],'-lz','-o',str(out/'estimate')],cwd=ROOT,check=True)
for p in (ROOT/'out/phase-fast30-v108').glob('*.bin'):shutil.copyfile(p,out/p.name)
files=['estimate']+[p.name for p in sorted(out.glob('*.bin'))];manifest={'architecture':'phase-major source8 and terminal1 stage candidates; horizontal terminal index, exact near, one corridor hub; prefetch cells; packed ports and coordinate scanner, buffered CSV','source_candidate_count':8,'fit_labels_used':False,'holdout_used':False,'prediction_cache':False,'hint_assets_serialized':False,'runtime_file_bytes':sum((out/f).stat().st_size for f in files),'command':'estimate -in requests.csv -out predictions.csv','compiler_flags':flags,'platform':'Apple M4/macOS local build; Linux not measured','files':{f:{'bytes':(out/f).stat().st_size,'sha256':hashlib.sha256((out/f).read_bytes()).hexdigest()} for f in files}}
assert manifest['runtime_file_bytes']<100000000;(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'directory':str(out),'runtime_file_bytes':manifest['runtime_file_bytes']}))
