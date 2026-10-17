"""Full validation of architecture-only tight potentials; no golden fitting."""
import json,re,subprocess,numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v127';_,y,_,_=load('validation');report={'state':'running','holdout_used':False,'fit_labels_used':False,'reference_potential_north':125,'new_north':127,'scale':12,'scope':'New periodic approximation, not physical-path certificate or final submission','candidates':[]}
for near in (False,True):
 for mode in (0,1,2):
  name=f'near{int(near)}-mode{mode}';dest=out/f'{name}.csv';log=out/f'{name}.stderr';cmd=[str(out/'estimate'),'--model',str(out/'tight.raw.bin'),'--mode',str(mode),'-in','out/evaluation/validation.request.csv','-out',str(dest)]
  if near:cmd+=['--near','out/phase-fast12-v116/core-template.bin']
  with log.open('w') as f:subprocess.run(['/usr/bin/time','-l',*cmd],cwd=ROOT,stderr=f,check=True)
  p=np.loadtxt(dest,delimiter=',',skiprows=1,usecols=2,dtype=np.int64);assert len(p)==150053;text=log.read_text();cpu=float(re.search(r'rows=\d+ cpu_seconds=([0-9.]+)',text)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',text)[1]);item={'name':name,'score':score(y,p),'cpu_seconds':cpu,'init_seconds':init,'query_seconds':cpu-init,'rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',text)[1]),'exact_fraction':float((p==y).mean())};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V127-tight-phase-models.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V127-tight-phase-models.json').write_text(json.dumps(report,indent=2)+'\n')
