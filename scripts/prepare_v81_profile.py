"""Freeze coupled architecture-only profile; no residual model reuse."""
import hashlib,json,re,shutil,subprocess
from architecture import ROOT
folder=ROOT/'out/phase-coupled-v81';folder.mkdir(exist_ok=True)
assert not (folder/'correction.bin').exists(),'Unexpected residual; this architecture profile is unlearned'
subprocess.run(['make','build/core_template_estimate'],cwd=ROOT,check=True);shutil.copy2(ROOT/'build/core_template_estimate',folder/'estimate')
for src,dst in [('out/architecture-benchmark/core-template-xz6.bin','core-template.bin'),('out/architecture-benchmark/vertical-transients-xz.bin','vertical-transients.bin'),('out/architecture-benchmark/horizontal-transients.bin','horizontal-transients.bin')]:shutil.copyfile(ROOT/src,folder/dst)
out=ROOT/'out/evaluation/validation.v81-profile.csv';r=subprocess.run(['/usr/bin/time','-l',str(folder/'estimate'),'-in','out/evaluation/validation.request.csv','-out',str(out)],cwd=ROOT,capture_output=True,text=True,check=True);(folder/'validation.log').write_text(r.stderr)
assert out.read_bytes()==(ROOT/'out/evaluation/validation.v81-1.csv').read_bytes()
files=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [folder/'estimate',folder/'core-template.bin',folder/'vertical-transients.bin',folder/'horizontal-transients.bin']]
manifest={'learned_residual':False,'cache_enabled':False,'validation_score':98.24991785308708,'full_validation_output_matches':True,'files':files,'runtime_file_bytes':sum(p['bytes'] for p in files),'cpu_seconds':float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]),'initialization_seconds':float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1]),'scope':'Architecture-only standalone research profile; not officialLinux or full billion acceptance. Goal99.9 still unachieved.'};assert manifest['runtime_file_bytes']<=100000000
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(ROOT/'reports/V81-standalone-profile.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
