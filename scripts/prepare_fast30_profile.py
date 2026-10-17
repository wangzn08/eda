"""Freeze C++ standard-input/output profile with architecture-only derived candidates."""
import hashlib,json,shutil,subprocess
from pathlib import Path
from architecture import ROOT
out=ROOT/'out/phase-fast30-v108';out.mkdir(exist_ok=True)
subprocess.run(['c++','-std=c++17','-O3','-Wall','-Wextra','-Wpedantic','-ffp-contract=off','-DCORE_PHASE_MAJOR=1','-DCORE_FAST30_PROFILE=1','-Isrc','src/core_template_estimate.cpp',*[str(p.relative_to(ROOT)) for p in sorted((ROOT/'build/xz').glob('*.o'))],'-lz','-o',str(out/'estimate')],cwd=ROOT,check=True)
assets={'core-template.bin':'core-template-xz6.bin','vertical-transients.bin':'vertical-transients-xz.bin','horizontal-transients.bin':'horizontal-transients.bin','vertical-far-delta.bin':'vertical-distant-delta-xz6.bin','joint-interaction.bin':'joint-transient-xz6.bin'}
for dest,source in assets.items():shutil.copyfile(ROOT/'out/architecture-benchmark'/source,out/dest)
files=['estimate']+list(assets)
manifest={'architecture':'Distant6 joint model, stage-specific single terminal candidate, exact near selection, one corridor hub, phase-major records; architecture-only candidate generation at initialization','fit_labels_used':False,'holdout_used':False,'prediction_cache':False,'runtime_file_bytes':sum((out/f).stat().st_size for f in files),'command':'estimate -in requests.csv -out predictions.csv','platform':'Local macOS C++17; official Linux acceptance not performed','files':{f:{'bytes':(out/f).stat().st_size,'sha256':hashlib.sha256((out/f).read_bytes()).hexdigest()} for f in files}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');assert manifest['runtime_file_bytes']<100000000
print(json.dumps({'directory':str(out),'runtime_file_bytes':manifest['runtime_file_bytes']},indent=2))
