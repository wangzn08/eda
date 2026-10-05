"""Rebuild selected128-tree research profile with standard interface, frozen assets."""
import hashlib,json,re,shutil,subprocess
from architecture import ROOT
folder=ROOT/'out/phase-piecewise-v85';folder.mkdir(exist_ok=True)
subprocess.run(['make','build/core_template_estimate'],cwd=ROOT,check=True)
cmd=['c++','-std=c++17','-O3','-ffp-contract=off','-DCORE_DEFAULT_TREES=128','-DCORE_DEFAULT_JOINT=1','-Isrc','src/core_template_estimate.cpp','build/xz/xz_crc32.o','build/xz/xz_dec_lzma2.o','build/xz/xz_dec_stream.o','-lz','-o',str(folder/'estimate')]
subprocess.run(cmd,cwd=ROOT,check=True)
for src,dst in [('out/architecture-benchmark/core-template-xz6.bin','core-template.bin'),('out/architecture-benchmark/vertical-transients-xz.bin','vertical-transients.bin'),('out/v84/correction-128.bin','correction.bin'),('out/architecture-benchmark/horizontal-transients.bin','horizontal-transients.bin'),('out/architecture-benchmark/vertical-far-delta-xz.bin','vertical-far-delta.bin')]:shutil.copyfile(ROOT/src,folder/dst)
out=ROOT/'out/evaluation/validation.v85-profile.csv'
r=subprocess.run(['/usr/bin/time','-l',str(folder/'estimate'),'-in','out/evaluation/validation.request.csv','-out',str(out)],cwd=ROOT,capture_output=True,text=True,check=True)
(folder/'validation.log').write_text(r.stderr)
reference=ROOT/'out/evaluation/validation.v84-128.csv';assert out.read_bytes()==reference.read_bytes()
files=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [folder/'estimate',folder/'core-template.bin',folder/'vertical-transients.bin',folder/'correction.bin',folder/'horizontal-transients.bin',folder/'vertical-far-delta.bin']]
manifest={'trees':128,'cache_enabled':False,'validation_score':98.89646091732914,'full_validation_output_matches':True,'files':files,'runtime_file_bytes':sum(p['bytes'] for p in files),'scope':'Frozen standalone research profile. OfficialLinux environment, full billion performance and99.9 precision goal remain unverified/unachieved.'}
assert manifest['runtime_file_bytes']<=100000000
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(ROOT/'reports/V85-standalone-profile.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
