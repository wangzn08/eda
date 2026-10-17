"""Serial throughput candidates; no holdout, full billion, or result cache."""
import subprocess,re,json,hashlib
from pathlib import Path
from architecture import ROOT
out=ROOT/'out/v109';report={'state':'running','target_seconds':900,'validation_floor':99,'scope':'M4 local extrapolation, development repeated 10m, init once','candidates':[]}
for name,binary,flags in [('io','out/v109/estimate-io',[]),('io-nohub','out/v109/estimate-io',['--corridor-hubs','0']),('prefetch','out/v109/estimate-prefetch',[]),('baseline','out/phase-fast30-v108/estimate',[])]:
 dest=out/(name+'-10m.csv');log=out/(name+'-10m.stderr')
 with log.open('w') as f:subprocess.run(['/usr/bin/time','-l',binary,*flags,'-in','out/evaluation/speed10m-v45.request.csv','-out',str(dest)],cwd=ROOT,stderr=f,check=True)
 text=log.read_text();cpu=float(re.search('cpu_seconds=([0-9.]+)',text)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',text)[1]);h=hashlib.sha256()
 with dest.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 item={'name':name,'cpu_seconds':cpu,'init_seconds':init,'query_seconds':cpu-init,'estimate_seconds':init+100*(cpu-init),'rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',text)[1]),'output_sha256':h.hexdigest()};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V109-fast15-pilot.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V109-fast15-pilot.json').write_text(json.dumps(report,indent=2)+'\n')
