"""Architecture-only mandatory critical-cycle families, full validation."""
import json,re,subprocess,numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v130';_,y,_,_=load('validation');report={'state':'running','holdout_used':False,'fit_labels_used':False,'scope':'Required cycle-family approximation; not a physical-path certificate','candidates':[]}
for tx,ty in ((30,36),(50,72),(70,120),(1000,1000)):
 for mode in (0,2):
  name=f'x{tx}-y{ty}-mode{mode}';dest=out/f'{name}.csv';log=out/f'{name}.stderr';cmd=[str(out/'estimate'),'--model',str(ROOT/'out/v128/required.raw.bin'),'--mode',str(mode),'--threshold-x',str(tx),'--threshold-y',str(ty),'--near','out/phase-fast12-v116/core-template.bin','-in','out/evaluation/validation.request.csv','-out',str(dest)]
  with log.open('w') as f:subprocess.run(['/usr/bin/time','-l',*cmd],cwd=ROOT,stderr=f,check=True)
  p=np.loadtxt(dest,delimiter=',',skiprows=1,usecols=2,dtype=np.int64);assert len(p)==150053;t=log.read_text();cpu=float(re.search(r'rows=\d+ cpu_seconds=([0-9.]+)',t)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',t)[1]);item={'name':name,'score':score(y,p),'cpu_seconds':cpu,'init_seconds':init,'query_seconds':cpu-init,'rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',t)[1]),'exact_fraction':float((p==y).mean())};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V130-quadrant-phase-models.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V130-quadrant-phase-models.json').write_text(json.dumps(report,indent=2)+'\n')
