import subprocess
from architecture import ROOT
base=['-std=c++17','-O3','-flto','-mcpu=apple-m4','-ffp-contract=off','-DCORE_PHASE_MAJOR=1','-DCORE_FAST30_PROFILE=1','-DCORE_FAST15_PROFILE=1','-DCORE_FAST12_PROFILE=1','-DCORE_BUFFERED_INPUT=1','-DCORE_PACKED_NEAR=1','-DCORE_BATCH_SIZE=16','-DCORE_PREFETCH=0','-DCORE_SHARED_CORRIDOR=1','-DCORE_BENCHMARK_SPLIT=150053']
for name,zero,prepared,fixed in [('control',0,0,0),('zero',1,0,1),('prepared',1,1,1)]:
 flags=base+[f'-DCORE_ZERO_COPY_BATCH={zero}',f'-DCORE_PREPARED={prepared}',f'-DCORE_FIXED_PORT_LOAD={fixed}'];subprocess.run(['c++',*flags,'-Isrc','src/core_template_estimate.cpp',*[str(p.relative_to(ROOT)) for p in sorted((ROOT/'build/xz').glob('*.o'))],'-lz','-o',f'out/v124/estimate-{name}'],cwd=ROOT,check=True);print(name,flush=True)
