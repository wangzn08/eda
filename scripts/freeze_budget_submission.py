"""Freeze only complete native runs that satisfy the 600 s novel-input budget."""
import argparse,hashlib,json,lzma,shutil,subprocess,tarfile
from pathlib import Path
from architecture import ROOT

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args();v=a.version
work=ROOT/f'out/v{v}';runtime=ROOT/f'out/runtime-budget-v{v}';target=ROOT/f'out/submission/final-v{v}';snapshot=work/'runtime-source'
profile=json.loads((ROOT/f'reports/V{v}-budget-profile.json').read_text());fit=json.loads((work/'runtime-manifest.json').read_text())
assert profile['state']=='complete' and len(profile['runs'])==3
assert profile['all_measured_speed_runs_under_budget'] and all(r['billion_estimate_cpu_seconds']<=600 for r in profile['runs'][1:])
assert profile['validation_score']>=99, 'Do not promote below the established 99-point floor'
assert profile['peak_rss_bytes']<=2000000000 and all(r['observed_runtime_threads']==1 for r in profile['runs'])
assert profile['runs'][0]['all_predictions_equal_offline']
assert profile['asset_sha256_before']==profile['asset_sha256_after']
assert not target.exists(),'Never overwrite a frozen release'
target.mkdir(parents=True);(target/'src').mkdir();(target/'generated').mkdir()
for name,h in profile['asset_sha256_before'].items():
 assert digest(runtime/name)==h;shutil.copy2(runtime/name,target/name)
for name,h in fit['runtime_source_sha256'].items():
 assert digest(snapshot/name)==h
 if name not in ('architecture_data.hpp','compiled_budget_residual.hpp'):shutil.copy2(snapshot/name,target/'src'/name)
# Architecture data is generated source, and is kept losslessly compressed.
# Rebuild expands it in a temporary source directory; runtime does no decoding.
arch=(snapshot/'architecture_data.hpp').read_bytes();packed=lzma.compress(arch,preset=9);assert lzma.decompress(packed)==arch
(target/'generated/architecture_data.hpp.xz').write_bytes(packed)
forest=(snapshot/'compiled_budget_residual.hpp').read_bytes();(target/'generated/compiled_budget_residual.hpp.xz').write_bytes(lzma.compress(forest,preset=9))
assert fit['profile'];profdata=(ROOT/fit['profile']).read_bytes();(target/'generated/development.profdata.xz').write_bytes(lzma.compress(profdata,preset=9))
definitions=[x for x in fit['compile_command'] if x.startswith('-D')]
config={'definitions':definitions,'entry':Path(fit['source_entry']).name,'architecture_header_sha256':hashlib.sha256(arch).hexdigest(),'forest_header_sha256':hashlib.sha256(forest).hexdigest(),'profile_sha256':hashlib.sha256(profdata).hexdigest()}
(target/'generated/build-config.json').write_text(json.dumps(config,indent=2)+'\n')
builder='''"""Rebuild the included snapshot using Python standard library only."""
import argparse,hashlib,json,lzma,platform,shlex,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--cxx',default='clang++');p.add_argument('--cxxflags',default='-O3 -std=c++17');p.add_argument('--archflags',default='-mcpu=apple-m4' if platform.system()=='Darwin' else '');p.add_argument('--lzma-cflags',default='-I/opt/homebrew/include' if platform.system()=='Darwin' else '');p.add_argument('--lzma-libs',default='/opt/homebrew/lib/liblzma.a' if platform.system()=='Darwin' else '-llzma');p.add_argument('--pgo',type=int,default=int(platform.system()=='Darwin'));a=p.parse_args();root=Path(__file__).resolve().parent
config=json.loads((root/'generated/build-config.json').read_text());arch=lzma.decompress((root/'generated/architecture_data.hpp.xz').read_bytes());assert hashlib.sha256(arch).hexdigest()==config['architecture_header_sha256']
with tempfile.TemporaryDirectory(prefix='eda-periodic-') as temporary:
 source=Path(temporary)/'src';shutil.copytree(root/'src',source);(source/'architecture_data.hpp').write_bytes(arch)
 forest=lzma.decompress((root/'generated/compiled_budget_residual.hpp.xz').read_bytes());assert hashlib.sha256(forest).hexdigest()==config['forest_header_sha256'];(source/'compiled_budget_residual.hpp').write_bytes(forest)
 profile=lzma.decompress((root/'generated/development.profdata.xz').read_bytes());assert hashlib.sha256(profile).hexdigest()==config['profile_sha256'];profile_path=Path(temporary)/'development.profdata';profile_path.write_bytes(profile)
 flags=[]
 for item in config['definitions']:
  if '_HEADER="' in item:
   key,value=item.split('=',1);item=key+'="'+str(source/Path(value.strip('"')).name)+'"'
  flags.append(item)
 command=shlex.split(a.cxx)+shlex.split(a.cxxflags)+['-flto','-ffp-contract=off']+shlex.split(a.archflags)+flags
 if a.pgo:command+=['-fprofile-instr-use='+str(profile_path)]
 command+=shlex.split(a.lzma_cflags)+['-I'+str(source),str(source/config['entry'])]+shlex.split(a.lzma_libs)+['-lz','-o',str(root/'estimate')]
 subprocess.run(command,cwd=root,check=True)
'''
(target/'rebuild.py').write_text(builder)
(target/'Makefile').write_text('''CXX = clang++
CXXFLAGS = -O3 -std=c++17
ifeq ($(shell uname -s),Darwin)
ARCHFLAGS ?= -mcpu=apple-m4
LZMA_CFLAGS ?= -I/opt/homebrew/include
LZMA_LIBS ?= /opt/homebrew/lib/liblzma.a
PGO ?= 1
else
ARCHFLAGS ?=
LZMA_CFLAGS ?=
LZMA_LIBS ?= -llzma
PGO ?= 0
endif
.PHONY: rebuild
rebuild:
\tpython3 rebuild.py --cxx='$(CXX)' --cxxflags='$(CXXFLAGS)' --archflags='$(ARCHFLAGS)' --lzma-cflags='$(LZMA_CFLAGS)' --lzma-libs='$(LZMA_LIBS)' --pgo=$(PGO)
''')
seconds=profile['pooled_billion_estimate_cpu_seconds']
(target/'README.md').write_text(f'''# V{v}: novel-request 600 second budget

Run `./estimate -in requests.csv -out predictions.csv` with all .bin files
beside the executable. Input: `From,To`; output: `From,To,delay` in ps.
The supplied binary is for Apple M4 / macOS ARM64.

Full 150053-row native validation score: {profile['validation_score']:.10f}.
This competition score is not the percentage of exactly correct answers.
Two disjoint 3000000-row novel request batches extrapolate to
{seconds:.6f} CPU seconds per billion, including one initialization and CSV.
Each measured batch must stay below 600 seconds for this release to freeze.
Peak RSS: {profile['peak_rss_bytes']} bytes. One runtime thread was observed.
These are local synthetic novel-request extrapolations, not official judge
results or a guarantee about another computer or hidden request distribution.

Architecture: periodic finite min-plus responses, fixed-layout terminal
selection and corridor costs, plus {fit['model']} with 56 inexpensive raw
geometry and static port features. Training uses development labels only.
The physical estimates are approximate. No final prediction cache or
intermediate operator cache is used. No golden labels are runtime assets.

`make rebuild` uses the captured source, generated tree and port metadata,
and development-only LLVM PGO profile. Python standard library expands the
lossless generated architecture and forest headers, plus the compiler profile,\nin a temporary source directory.
LightGBM and training inputs are not needed to rebuild. Compiler, zlib and
liblzma are required. PGO profile was produced with Apple Clang 21.
Linux example: `make rebuild CXX=g++ ARCHFLAGS= LZMA_CFLAGS= LZMA_LIBS=-llzma PGO=0`.
Linux performance is unmeasured. The distributed binary is the measured one.
''')
sources={str(p.relative_to(target)):digest(p) for p in target.rglob('*') if p.is_file() and p.name not in profile['asset_sha256_before']}
manifest={'version':v,'release_kind':'novel-budget','runtime_asset_sha256':profile['asset_sha256_before'],'source_sha256':sources,'shared_asset_roots':['artifacts/runtime-periodic-v158','artifacts/runtime-v219'],'benchmark_profile':f'reports/V{v}-budget-profile.json','validation_score':profile['validation_score'],'billion_cpu_seconds':seconds,'hard_budget_seconds':600,'architecture_header_sha256':config['architecture_header_sha256'],'pgo_scope':'700705 development requests only; no labels supplied to instrumented executable','pgo_profile_sha256':hashlib.sha256(profdata).hexdigest()}
(target/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
size=sum(p.stat().st_size for p in target.rglob('*') if p.is_file());assert size<=100000000,size
# A frozen release must independently rebuild to the actual measured machine code.
from audit_score_submission import macho
reference=(target/'estimate').read_bytes();permissions=(target/'estimate').stat().st_mode
try:
 with (work/'standalone-rebuild.stdout').open('w') as out,(work/'standalone-rebuild.stderr').open('w') as err:subprocess.run(['make','rebuild'],cwd=target,stdout=out,stderr=err,check=True)
 rebuilt=(target/'estimate').read_bytes();left,ls=macho(reference);right,rs=macho(rebuilt)
 proof={'measured_sha256':hashlib.sha256(reference).hexdigest(),'rebuilt_sha256':hashlib.sha256(rebuilt).hexdigest(),'all_file_backed_sections_identical':ls==rs,'identical_except_uuid_and_signature':left==right}
 (work/'rebuild-parity.json').write_text(json.dumps(proof,indent=2)+'\n');assert proof['all_file_backed_sections_identical'] and proof['identical_except_uuid_and_signature']
finally:(target/'estimate').write_bytes(reference);(target/'estimate').chmod(permissions)
for name,h in {**profile['asset_sha256_before'],**sources}.items():assert digest(target/name)==h
# Save large unchanged architecture files once. The source-hints asset already
# exists in V219; all other periodic model assets are shared by budget releases.
common=ROOT/'artifacts/runtime-periodic-v158';common.mkdir(exist_ok=True);release=ROOT/f'artifacts/runtime-v{v}';assert not release.exists();release.mkdir()
for source in target.rglob('*'):
 if not source.is_file():continue
 name=str(source.relative_to(target))
 if source.name in profile['asset_sha256_before'] and source.name!='estimate':
  old=ROOT/'artifacts/runtime-v219'/source.name
  destination=old if old.exists() and digest(old)==digest(source) else common/source.name
 else:destination=release/name
 if destination.exists():assert digest(destination)==digest(source)
 else:destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
archive=ROOT/f'out/submission/fpga-delay-v{v}.tar.gz'
with tarfile.open(archive,'w:gz') as tar:tar.add(target,arcname=target.name)
with tarfile.open(archive) as tar:
 members=[m for m in tar.getmembers() if m.isfile()];assert sum(m.size for m in members)==size
 for member in members:
  relative=Path(member.name).relative_to(target.name);assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==digest(target/relative)
report={'state':'complete','version':v,'validation_score':profile['validation_score'],'billion_estimate_cpu_seconds':[r['billion_estimate_cpu_seconds'] for r in profile['runs'][1:]],'pooled_billion_estimate_cpu_seconds':seconds,'peak_rss_bytes':profile['peak_rss_bytes'],'complete_submission_bytes':size,'archive_bytes':archive.stat().st_size,'archive_sha256':digest(archive),'single_runtime_thread_observed':True,'all_validation_predictions_equal_independent_python':True,'same_frozen_runtime_for_all_runs':True,'rebuild_machine_code_identical':True,'prediction_cache':False,'architecture_operator_cache':False}
(ROOT/f'reports/V{v}-budget-submission.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
