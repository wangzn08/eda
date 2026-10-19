"""Rebuild using only included files and Python standard library."""
import argparse,platform,shlex,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--cxx',default='clang++');p.add_argument('--cxxflags',default='-O3 -std=c++17');p.add_argument('--archflags',default='-mcpu=apple-m4' if platform.system()=='Darwin' else '');p.add_argument('--lzma-cflags',default='-I/opt/homebrew/include' if platform.system()=='Darwin' else '');p.add_argument('--lzma-libs',default='/opt/homebrew/lib/liblzma.a' if platform.system()=='Darwin' else '-llzma');a=p.parse_args();root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='eda-forest-') as directory:
 header=Path(directory)/'compiled_selected_forest.hpp'
 subprocess.run([sys.executable,str(root/'generate_forest.py'),str(root/'correction.bin'),str(header),'--domains','2'],check=True)
 flags=['-DCORE_LIBLZMA=1','-DROUTING_GRAPH_ONLY=1','-DRUNTIME_COMPONENT_PROFILE=0','-DRUNTIME_COMPILED_FOREST=1','-DRUNTIME_TERMINAL_MASKS=1','-DRUNTIME_INTERVAL_MASKS=1','-DRUNTIME_OPERATOR_CACHE=0','-DRUNTIME_SHORT_PACK_VERIFY=0','-DRUNTIME_CORRECTION_GATE=1','-DRUNTIME_BATCH_SIZE=64','-DRUNTIME_REFINED_TERMINALS=1','-DRUNTIME_MASK_HOT_CODEC=1','-DRUNTIME_MASK_DIRECT=0',f'-DRUNTIME_COMPILED_FOREST_HEADER="{header}"']
 command=shlex.split(a.cxx)+shlex.split(a.cxxflags)+shlex.split(a.archflags)+flags+shlex.split(a.lzma_cflags)+[str(root/'src/runtime_route_estimate.cpp')]+shlex.split(a.lzma_libs)+['-lz','-o',str(root/'estimate')]
 subprocess.run(command,cwd=root,check=True)
