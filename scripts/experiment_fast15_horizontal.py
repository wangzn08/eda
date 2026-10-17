"""Architecture-only source selection; serial full validation and10m timing."""
import subprocess,csv,re,json,hashlib
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v109';_,y,_,_=load('validation');report={'state':'running','holdout_used':False,'fit_labels_used':False,'prediction_cache':False,'target_seconds':900,'candidates':[]}
for name,count in [('horizontal-source8',8),('horizontal-source4',4)]:
 cmd=['out/v109/estimate-horizontal','--horizontal-hints','--source-hints',str(count),'--packed-ports'];val=out/(name+'-validation.csv');vlog=out/(name+'-validation.stderr')
 with vlog.open('w') as f:subprocess.run(['/usr/bin/time','-l',*cmd,'-in','out/evaluation/validation.request.csv','-out',str(val)],cwd=ROOT,stderr=f,check=True)
 with val.open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
 item={'name':name,'source_count':count,'score':score(y,p),'validation_rows':len(p)};assert len(p)==150053
 if item['score']>=99:
  dest=out/(name+'-10m.csv');log=out/(name+'-10m.stderr')
  with log.open('w') as f:subprocess.run(['/usr/bin/time','-l',*cmd,'-in','out/evaluation/speed10m-v45.request.csv','-out',str(dest)],cwd=ROOT,stderr=f,check=True)
  text=log.read_text();cpu=float(re.search('cpu_seconds=([0-9.]+)',text)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',text)[1]);h=hashlib.sha256()
  with dest.open('rb') as f:
   for block in iter(lambda:f.read(1<<20),b''):h.update(block)
  item.update(cpu_seconds=cpu,init_seconds=init,query_seconds=cpu-init,estimate_seconds=init+100*(cpu-init),rss_bytes=int(re.search(r'(\d+)\s+maximum resident set size',text)[1]),output_sha256=h.hexdigest())
 report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V110-fast15-horizontal.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V110-fast15-horizontal.json').write_text(json.dumps(report,indent=2)+'\n')
