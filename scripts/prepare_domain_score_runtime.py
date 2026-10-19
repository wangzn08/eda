"""Freeze numeric domain experts into a standard standalone runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

import lightgbm as lgb

from architecture import ROOT

p=argparse.ArgumentParser()
p.add_argument('--version',required=True)
p.add_argument('--features',required=True)
p.add_argument('--models',nargs='+',required=True)
p.add_argument('--trees',type=int,required=True)
p.add_argument('--gate')
p.add_argument('--gate-mapping')
p.add_argument('--gate-threshold',type=float,default=.1)
p.add_argument('--source',default='src/runtime_route_estimate.cpp')
p.add_argument('--batch-size',type=int,default=32)
p.add_argument('--refined-terminals',action='store_true')
p.add_argument('--hot-terminal-codec',action='store_true')
p.add_argument('--direct-terminal-masks',action='store_true')
a=p.parse_args()
assert len(a.models) in (1,2,4)
work=ROOT/f'out/v{a.version}';work.mkdir(exist_ok=True)
folder=ROOT/f'out/runtime-kernel-v{a.version}';folder.mkdir(exist_ok=True)
names=json.loads((ROOT/a.features).read_text())
parts=[]
for index,model_file in enumerate(a.models):
 model=lgb.Booster(model_file=str(ROOT/model_file));short=work/f'expert-{index}.txt';model.save_model(str(short),num_iteration=a.trees)
 binary=work/f'expert-{index}.bin'
 subprocess.run([sys.executable,'scripts/export_selected_forest.py',str(short),str(ROOT/a.features),str(binary),'--schema',str(work/'selected_feature_schema.hpp')],cwd=ROOT,check=True)
 parts.append(binary.read_bytes())
assert all(part[:140]==parts[0][:140] for part in parts)
trees=sum(struct.unpack_from('<I',part,140)[0] for part in parts)
assert trees<=64
body=parts[0][:140]+struct.pack('<I',trees)+b''.join(part[144:] for part in parts)
(folder/'correction.bin').write_bytes(body)
compiled=work/'compiled_selected_forest.hpp'
subprocess.run([sys.executable,'scripts/export_compiled_selected_forest.py',str(folder/'correction.bin'),str(compiled),'--domains',str(len(parts))],cwd=ROOT,check=True)
for source in (ROOT/'out/runtime-kernel-v242').iterdir():
 if source.is_file() and source.name not in ('estimate','correction.bin'):
  target=folder/source.name
  if not target.exists():os.link(source,target)
flags=['-O3','-mcpu=apple-m4','-std=c++17','-DCORE_LIBLZMA=1','-DROUTING_GRAPH_ONLY=1','-DRUNTIME_COMPONENT_PROFILE=0','-DRUNTIME_COMPILED_FOREST=1','-DRUNTIME_TERMINAL_MASKS=1','-DRUNTIME_INTERVAL_MASKS=1','-DRUNTIME_OPERATOR_CACHE=0','-DRUNTIME_SHORT_PACK_VERIFY=0',f'-DRUNTIME_FEATURE_SCHEMA_HEADER="{work}/selected_feature_schema.hpp"',f'-DRUNTIME_COMPILED_FOREST_HEADER="{compiled}"']
if a.gate:
 assert a.gate_mapping
 gate_header=work/'compiled_selected_correction_gate.hpp'
 subprocess.run([sys.executable,'scripts/export_selected_correction_gate.py',str(ROOT/a.gate),str(ROOT/a.gate_mapping),str(gate_header),'--threshold',str(a.gate_threshold)],cwd=ROOT,check=True)
 flags+=['-DRUNTIME_CORRECTION_GATE=1',f'-DRUNTIME_CORRECTION_GATE_HEADER="{gate_header}"']
else:flags+=['-DRUNTIME_CORRECTION_GATE=0']
flags+=[f'-DRUNTIME_BATCH_SIZE={a.batch_size}']
flags+=[f'-DRUNTIME_REFINED_TERMINALS={int(a.refined_terminals)}']
flags+=[f'-DRUNTIME_MASK_HOT_CODEC={int(a.hot_terminal_codec)}']
flags+=[f'-DRUNTIME_MASK_DIRECT={int(a.direct_terminal_masks)}']
snapshot=work/'runtime-source';snapshot.mkdir(exist_ok=True)
import shutil
for source in (ROOT/'out/submission/final-v242/src').iterdir():
 if source.name not in ('compiled_selected_forest.hpp','compiled_selected_correction_gate.hpp','selected_feature_schema.hpp','runtime_route_estimate.cpp'):
  shutil.copy2(ROOT/'src'/source.name,snapshot/source.name)
for name in ('selected_feature_schema.hpp','compiled_selected_forest.hpp','compiled_selected_correction_gate.hpp'):
 if (work/name).exists():shutil.copy2(work/name,snapshot/name)
shutil.copy2(ROOT/'src/selected_physics_features.hpp',snapshot/'selected_physics_features.hpp')
shutil.copy2(ROOT/a.source,snapshot/'runtime_route_estimate.cpp')
command=['clang++',*flags,'-I/opt/homebrew/include','-I'+str(ROOT/'src'),str(ROOT/a.source),'/opt/homebrew/lib/liblzma.a','-lz','-o',str(folder/'estimate')]
subprocess.run(command,cwd=ROOT,check=True)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
source_hash={p.name:digest(p) for p in snapshot.iterdir() if p.is_file()}
(work/'runtime-source-sha256.json').write_text(json.dumps(source_hash,indent=2)+'\n')
manifest={'version':a.version,'domains':len(parts),'trees_per_request':a.trees,'total_trees':trees,'features':len(names),'models':a.models,'feature_names':a.features,'gate_model':a.gate,'gate_threshold':a.gate_threshold if a.gate else None,'batch_size':a.batch_size,'refined_terminals':a.refined_terminals,'hot_terminal_codec':a.hot_terminal_codec,'direct_terminal_masks':a.direct_terminal_masks,'source_entry':a.source,'architecture_operator_cache':False,'prediction_cache':False,'fit_scope':'development only','holdout_used':False,'compile_command':command,'runtime_source_sha256':source_hash,'files':{p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in folder.iterdir() if p.is_file()}}
(work/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'directory':str(folder),'runtime_bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file()),'version':a.version}),flush=True)
