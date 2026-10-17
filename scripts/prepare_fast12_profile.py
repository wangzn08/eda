"""Freeze measured compact layout; preserve the previous 15-minute profile."""
import hashlib,json,shutil,subprocess,argparse
from architecture import ROOT
p=argparse.ArgumentParser();p.add_argument('--directory',default='out/phase-fast12-v115');p.add_argument('--target-horizontal',action='store_true');p.add_argument('--batch',type=int,default=32);p.add_argument('--shared',action='store_true');a=p.parse_args()
out=ROOT/a.directory;out.mkdir(exist_ok=True)
flags=['-std=c++17','-O3','-flto','-mcpu=apple-m4','-ffp-contract=off','-DCORE_PHASE_MAJOR=1','-DCORE_FAST30_PROFILE=1','-DCORE_FAST15_PROFILE=1','-DCORE_FAST12_PROFILE=1','-DCORE_BUFFERED_INPUT=1','-DCORE_PACKED_NEAR=1','-DCORE_PREFETCH=0',f'-DCORE_BATCH_SIZE={a.batch}',f'-DCORE_SHARED_CORRIDOR={int(a.shared)}',f'-DCORE_FAST12_TARGET={int(a.target_horizontal)}']
subprocess.run(['c++',*flags,'-Isrc','src/core_template_estimate.cpp',*[str(q.relative_to(ROOT)) for q in sorted((ROOT/'build/xz').glob('*.o'))],'-lz','-o',str(out/'estimate')],cwd=ROOT,check=True)
for q in (ROOT/'out/phase-fast15-v112').glob('*.bin'):shutil.copyfile(q,out/q.name)
files=['estimate']+[q.name for q in sorted(out.glob('*.bin'))]
m={'state':'candidate pending full benchmark','compiler_flags':flags,'command':'estimate -in requests.csv -out predictions.csv','source_candidates':8,'terminal_candidates':1,'compact_coefficients':True,'target_horizontal':a.target_horizontal,'shared_corridor':a.shared,'batch':a.batch,'prediction_cache':False,'holdout_used':False,'platform':'Apple M4/macOS; official Linux not measured','files':{f:{'bytes':(out/f).stat().st_size,'sha256':hashlib.sha256((out/f).read_bytes()).hexdigest()} for f in files}}
m['runtime_file_bytes']=sum(v['bytes'] for v in m['files'].values());assert m['runtime_file_bytes']<=100000000;(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'directory':str(out),'bytes':m['runtime_file_bytes']}))
