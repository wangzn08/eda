"""Rebuild the included snapshot using Python standard library only."""
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
