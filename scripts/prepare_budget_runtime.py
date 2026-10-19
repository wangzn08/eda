"""Build a V158-derived novel-request candidate; keep old snapshots immutable."""
import argparse,json,os,subprocess,hashlib,shutil,re,shlex
from pathlib import Path
from architecture import ROOT
p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--model');p.add_argument('--source-hint-count',type=int,default=8,choices=(4,8));p.add_argument('--source-hint-asset');p.add_argument('--cutoff',type=float,default=0);p.add_argument('--batch-size',type=int,default=32);p.add_argument('--pgo',action='store_true');p.add_argument('--instrument',action='store_true');p.add_argument('--simd-near',action='store_true');p.add_argument('--profile');p.add_argument('--source',default='src/budget_route_estimate.cpp');p.add_argument('--legacy-entry',action='store_true');a=p.parse_args()
assert not (ROOT/f'artifacts/runtime-v{a.version}').exists(), 'Frozen versions are immutable; choose a new version'
assert not (ROOT/f'out/v{a.version}/runtime-manifest.json').exists(), 'Do not overwrite a captured build; choose a new version'
folder=ROOT/f'out/runtime-budget-v{a.version}';folder.mkdir(exist_ok=True);work=ROOT/f'out/v{a.version}';work.mkdir(exist_ok=True)
header=None;metadata=None
if a.model:
 metadata_path=(ROOT/a.model).parent/'port-metadata.json'
 if metadata_path.exists():
  data=json.loads(metadata_path.read_text());assert len(data)==496 and all(len(row)==8 for row in data)
  metadata=work/'budget_port_metadata.hpp';metadata.write_text('#pragma once\nstatic constexpr int16_t budget_port_metadata[496][8]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in data)+'};\n')
if a.model:
 header=work/'compiled_budget_residual.hpp';subprocess.run([str(ROOT/'out/research-env/bin/python'),'scripts/export_budget_residual.py',a.model,str(header),'--cutoff',str(a.cutoff)],cwd=ROOT,check=True)
for source in (ROOT/'out/phase-fast10-v158').iterdir():
 if source.name!='estimate' and not (folder/source.name).exists():os.link(ROOT/a.source_hint_asset if source.name=='source-hints.bin' and a.source_hint_asset else source,folder/source.name)
flags=['-O3','-flto','-mcpu=apple-m4','-ffp-contract=off','-std=c++17','-DCORE_LIBLZMA=1','-DCORE_PHASE_MAJOR=1','-DCORE_PACKED_NEAR=1',f'-DCORE_BATCH_SIZE={a.batch_size}','-DCORE_SHARED_CORRIDOR=1','-DCORE_FIXED_PORT_LOAD=1','-DCORE_PREPARED_GEOMETRY=1','-DCORE_LOAD_HINT_ASSETS=1','-DCORE_SPARSE_SOURCE_ITERATION=1','-DCORE_HINT_PHASE_SCAN=1','-DROUTING_GRAPH_ONLY=1']
flags+=[f'-DBUDGET_SOURCE_HINTS={a.source_hint_count}']
if a.legacy_entry:
 flags=[x for x in flags if x!='-DROUTING_GRAPH_ONLY=1']+[f'-D{k}=1' for k in ['CORE_FAST30_PROFILE','CORE_FAST15_PROFILE','CORE_FAST12_PROFILE','CORE_BUFFERED_INPUT','CORE_ZERO_COPY_BATCH','CORE_PREPARED']]
if a.simd_near:flags+=['-DCORE_SIMD_NEAR_HINTS=1']
if a.instrument:flags+=['-fprofile-instr-generate']
if a.profile:flags+=['-fprofile-instr-use='+str(ROOT/a.profile)]
if a.pgo:flags+=['-fprofile-instr-use='+str(ROOT/'out/v157/development.profdata'),'-Wno-profile-instr-out-of-date','-Wno-profile-instr-unprofiled']
if metadata:flags+=[f'-DBUDGET_PORT_METADATA_HEADER="{metadata}"']
if header:flags+=[f'-DBUDGET_RESIDUAL_HEADER="{header}"']
command=['clang++',*flags,'-I/opt/homebrew/include','-I'+str(ROOT/'src'),str(ROOT/a.source),'/opt/homebrew/lib/liblzma.a','-lz','-o',str(folder/'estimate')];subprocess.run(command,cwd=ROOT,check=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Capture only compiler-active local includes. Graph-only builds exclude the
# multi-megabyte lower-bound research headers behind preprocessor conditions.
snapshot=work/'runtime-source';snapshot.mkdir(exist_ok=True)
deps=subprocess.check_output(['clang++',*flags,'-I/opt/homebrew/include','-I'+str(ROOT/'src'),'-MM','-MT','capture',str(ROOT/a.source)],cwd=ROOT,text=True)
paths=shlex.split(deps.replace('\\\n','').split(':',1)[1])
for item in paths:
 path=Path(item)
 if path.is_relative_to(ROOT) and path.is_file():shutil.copy2(path,snapshot/path.name)
manifest={'version':a.version,'architecture':'V158 periodic min-plus plus optional tiny compiled residual','batch_size':a.batch_size,'source_hint_count':a.source_hint_count,'source_hint_asset':a.source_hint_asset,'pgo':a.pgo,'instrument':a.instrument,'simd_near_hints':a.simd_near,'profile':a.profile,'source_entry':a.source,'legacy_entry':a.legacy_entry,'model':a.model,'cutoff':a.cutoff,'prediction_cache':False,'architecture_operator_cache':False,'holdout_used':False,'compile_command':command,'runtime_source_sha256':{p.name:digest(p) for p in snapshot.iterdir()},'files':{p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in folder.iterdir() if p.is_file()}}
(work/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'version':a.version,'runtime_bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file())}),flush=True)
