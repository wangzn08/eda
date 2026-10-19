"""Create a self-contained <100 MB submission with stdlib source regeneration."""
import argparse,hashlib,json,shutil,tarfile
from pathlib import Path
from architecture import ROOT

p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args()
work=ROOT/f'out/v{a.version}';runtime=ROOT/f'out/runtime-kernel-v{a.version}';target=ROOT/f'out/submission/final-v{a.version}'
assert not target.exists(),'Never overwrite a frozen submission'
manifest=json.loads((work/'runtime-manifest.json').read_text())
profile=json.loads((ROOT/f'reports/V{a.version}-native-score-profile.json').read_text());assert profile['state']=='complete'
target.mkdir(parents=True);(target/'src').mkdir()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for name,data in manifest['files'].items():
 assert digest(runtime/name)==data['sha256'];shutil.copy2(runtime/name,target/name)
# Same source closure as V242, replacing the schema and adding interactions.
# The generated forest is recreated from the included correction.bin at build
# time in a temporary directory, so the submission does not contain two full
# representations of the same model.
snapshot=work/'runtime-source'
source_hashes=json.loads((work/'runtime-source-sha256.json').read_text())
for name,expected in source_hashes.items():
 assert digest(snapshot/name)==expected
 if name!='compiled_selected_forest.hpp':shutil.copy2(snapshot/name,target/'src'/name)
shutil.copy2(ROOT/'scripts/export_compiled_selected_forest.py',target/'generate_forest.py')
builder='''"""Rebuild using only included files and Python standard library."""
import argparse,platform,shlex,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--cxx',default='clang++');p.add_argument('--cxxflags',default='-O3 -std=c++17');p.add_argument('--archflags',default='-mcpu=apple-m4' if platform.system()=='Darwin' else '');p.add_argument('--lzma-cflags',default='-I/opt/homebrew/include' if platform.system()=='Darwin' else '');p.add_argument('--lzma-libs',default='/opt/homebrew/lib/liblzma.a' if platform.system()=='Darwin' else '-llzma');a=p.parse_args();root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='eda-forest-') as directory:
 header=Path(directory)/'compiled_selected_forest.hpp'
 subprocess.run([sys.executable,str(root/'generate_forest.py'),str(root/'correction.bin'),str(header),'--domains','__DOMAIN_COUNT__'],check=True)
 flags=['-DCORE_LIBLZMA=1','-DROUTING_GRAPH_ONLY=1','-DRUNTIME_COMPONENT_PROFILE=0','-DRUNTIME_COMPILED_FOREST=1','-DRUNTIME_TERMINAL_MASKS=1','-DRUNTIME_INTERVAL_MASKS=1','-DRUNTIME_OPERATOR_CACHE=0','-DRUNTIME_SHORT_PACK_VERIFY=0','-DRUNTIME_CORRECTION_GATE=__GATE_ENABLED__','-DRUNTIME_BATCH_SIZE=__BATCH_SIZE__','-DRUNTIME_REFINED_TERMINALS=__REFINED_ENABLED__','-DRUNTIME_MASK_HOT_CODEC=__HOT_CODEC_ENABLED__','-DRUNTIME_MASK_DIRECT=__DIRECT_ENABLED__','-DRUNTIME_ENDPOINT_SEEDS=__SEEDS_ENABLED__','-DRUNTIME_ENDPOINT_BELLMAN=__ENDPOINT_MODE__','-DRUNTIME_PATH_ENVELOPE=__PATH_ENVELOPE__','-DRUNTIME_CORRECTION_FALLBACK=__FALLBACK_ENABLED__',f'-DRUNTIME_COMPILED_FOREST_HEADER="{header}"']
 command=shlex.split(a.cxx)+shlex.split(a.cxxflags)+shlex.split(a.archflags)+flags+shlex.split(a.lzma_cflags)+[str(root/'src/runtime_route_estimate.cpp')]+shlex.split(a.lzma_libs)+['-lz','-o',str(root/'estimate')]
 subprocess.run(command,cwd=root,check=True)
'''.replace('__DOMAIN_COUNT__',str(manifest['domains'])).replace('__GATE_ENABLED__',str(int(bool(manifest['gate_model'])))).replace('__BATCH_SIZE__',str(manifest.get('batch_size',32))).replace('__REFINED_ENABLED__',str(int(manifest.get('refined_terminals',False)))).replace('__HOT_CODEC_ENABLED__',str(int(manifest.get('hot_terminal_codec',False)))).replace('__DIRECT_ENABLED__',str(int(manifest.get('direct_terminal_masks',False)))).replace('__SEEDS_ENABLED__',str(int(manifest.get('endpoint_mode',0)==6))).replace('__ENDPOINT_MODE__',str(manifest.get('endpoint_mode',0))).replace('__PATH_ENVELOPE__',str(int(manifest.get('path_envelope',False)))).replace('__FALLBACK_ENABLED__',str(int(manifest.get('fallback_v254',False))))
(target/'rebuild.py').write_text(builder)
(target/'Makefile').write_text('''CXX = clang++
CXXFLAGS = -O3 -std=c++17
ifeq ($(shell uname -s),Darwin)
ARCHFLAGS ?= -mcpu=apple-m4
LZMA_CFLAGS ?= -I/opt/homebrew/include
LZMA_LIBS ?= /opt/homebrew/lib/liblzma.a
else
ARCHFLAGS ?=
LZMA_CFLAGS ?=
LZMA_LIBS ?= -llzma
endif
.PHONY: rebuild
rebuild:
\tpython3 rebuild.py --cxx='$(CXX)' --cxxflags='$(CXXFLAGS)' --archflags='$(ARCHFLAGS)' --lzma-cflags='$(LZMA_CFLAGS)' --lzma-libs='$(LZMA_LIBS)'
''')
embedded_forest=sum(p.stat().st_size for p in target.rglob('*') if p.is_file())+(snapshot/'compiled_selected_forest.hpp').stat().st_size+15000<=100000000
if embedded_forest:
 shutil.copy2(snapshot/'compiled_selected_forest.hpp',target/'src/compiled_selected_forest.hpp')
 for name in ('generate_forest.py','rebuild.py'):(target/name).unlink()
 flags=['-DCORE_LIBLZMA=1','-DROUTING_GRAPH_ONLY=1','-DRUNTIME_COMPONENT_PROFILE=0','-DRUNTIME_COMPILED_FOREST=1','-DRUNTIME_TERMINAL_MASKS=1','-DRUNTIME_INTERVAL_MASKS=1','-DRUNTIME_OPERATOR_CACHE=0','-DRUNTIME_SHORT_PACK_VERIFY=0',f"-DRUNTIME_CORRECTION_GATE={int(bool(manifest['gate_model']))}",f"-DRUNTIME_BATCH_SIZE={manifest.get('batch_size',32)}",f"-DRUNTIME_REFINED_TERMINALS={int(manifest.get('refined_terminals',False))}",f"-DRUNTIME_MASK_HOT_CODEC={int(manifest.get('hot_terminal_codec',False))}",f"-DRUNTIME_MASK_DIRECT={int(manifest.get('direct_terminal_masks',False))}",f"-DRUNTIME_ENDPOINT_SEEDS={int(manifest.get('endpoint_mode',0)==6)}",f"-DRUNTIME_ENDPOINT_BELLMAN={manifest.get('endpoint_mode',0)}",f"-DRUNTIME_PATH_ENVELOPE={int(manifest.get('path_envelope',False))}",f"-DRUNTIME_CORRECTION_FALLBACK={int(manifest.get('fallback_v254',False))}"]
 makefile=(target/'Makefile').read_text().split('.PHONY: rebuild')[0]
 makefile+='DEFINES = '+' '.join(flags)+'\n.PHONY: rebuild\nrebuild:\n\t$(CXX) $(CXXFLAGS) $(ARCHFLAGS) $(DEFINES) $(LZMA_CFLAGS) src/runtime_route_estimate.cpp $(LZMA_LIBS) -lz -o estimate\n'
 (target/'Makefile').write_text(makefile)
if manifest.get('endpoint_mode'):
 assert all(r['billion_estimate_cpu_seconds']<=3600 for r in profile['runs'][1:]),'Do not freeze a release beyond the one-hour CPU limit'
 assert profile['peak_rss_bytes']<=2000000000
seconds=profile['pooled_billion_estimate_cpu_seconds']
build_description=('The exact generated forest header is included. No Python packages or training data are needed to rebuild.' if embedded_forest else 'Python 3 standard library regenerates the forest header from correction.bin in a temporary directory; LightGBM and training data are not required.')
model_description=('The existing single residual forest and shallow gate are retained.' if manifest['domains']==1 else 'One development-trained numeric expert is selected by whether the chosen route crosses the vertical wall.')
feature_description=('The model uses137 geometry, response and endpoint-potential features.' if manifest['features']==137 else 'The model also uses integer endpoint/curve interaction features.')
if manifest.get('endpoint_mode'):feature_description='The model uses137 original features and16 actual endpoint Bellman/beam profile features; these are approximate, not shortest-path certificates.'
if manifest.get('fallback_v254'):model_description+=' A development cross-fitted expected-gain gate selects the physical expert; other requests use the frozen V254 forest/gate.'
(target/'README.md').write_text(f'''# V{a.version} score-oriented runtime

Standard entry: `./estimate -in requests.csv -out predictions.csv`.
Input header: `From,To`; output: `From,To,delay`.

The prebuilt executable is Apple M4/macOS ARM64. Full validation score:
{profile['validation_score']:.10f}. The competition score is not an exact-match percentage.
Two serial runs use disjoint synthetic, nonrepeated requests newly recombined
from development pins. Their local single-thread CPU extrapolation to one
billion requests, including one initialization and CSV I/O, averages
{seconds:.4f} seconds ({seconds/60:.4f} minutes). This is not an official
hidden-input or Linux result. Peak runtime RSS: {profile['peak_rss_bytes']} bytes.

Physical short-distance/response kernels select the route. {model_description}
{feature_description}
The intermediate operator cache is disabled; no final prediction cache or
golden answers are read. Gate enabled: {bool(manifest['gate_model'])}.

Keep estimate, all five .bin files and the liblzma license together.
The included source closure can be rebuilt with `make rebuild`; it needs a
C++17 compiler, zlib and liblzma. {build_description}

On Linux: `make rebuild CXX=g++ ARCHFLAGS= LZMA_CFLAGS= LZMA_LIBS=-llzma`.
Linux performance has not been measured. Rebuilding can change the Mach-O UUID
and code signature; the distributed executable is the one actually measured.
''')
source_hash={str(p.relative_to(target)):digest(p) for p in target.rglob('*') if p.is_file() and p.name not in manifest['files']}
proof={'version':a.version,'runtime_asset_sha256':{name:data['sha256'] for name,data in manifest['files'].items()},'source_sha256':source_hash,'domains':manifest['domains'],'trees_per_request':manifest['trees_per_request'],'generated_forest_included':embedded_forest,'generated_forest_reconstructed_from':None if embedded_forest else 'correction.bin','python_packages_for_rebuild':'not required' if embedded_forest else 'standard library only','benchmark_profile':f'reports/V{a.version}-native-score-profile.json'}
(target/'BUILD_MANIFEST.json').write_text(json.dumps(proof,indent=2)+'\n')
files=[p for p in target.rglob('*') if p.is_file()];size=sum(p.stat().st_size for p in files)
assert size<=100000000,size
archive=ROOT/f'out/submission/fpga-delay-v{a.version}.tar.gz'
with tarfile.open(archive,'w:gz') as tar:tar.add(target,arcname=target.name)
with tarfile.open(archive,'r:gz') as tar:
 for member in tar.getmembers():
  if member.isfile():
   source=target/Path(member.name).relative_to(target.name)
   assert tar.extractfile(member).read()==source.read_bytes()
report={'state':'complete','version':a.version,'complete_submission_bytes':size,'file_count':len(files),'archive_bytes':archive.stat().st_size,'archive_sha256':digest(archive),'all_archive_members_match':True,'runtime_assets_match_measured':True,'build_manifest':proof}
(ROOT/f'reports/V{a.version}-submission-integrity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='build_manifest'},indent=2))
