"""Compare fused records, pipelined batches, compact indices, and adaptive routes."""
import csv,hashlib,json,re,subprocess
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v113';_,y,_,_=load('validation');report={'state':'running','target_seconds':720,'validation_floor':99,'holdout_used':False,'fit_labels_used':False,'prediction_cache':False,'scope':'Serial full validation and development1m screening; final10m required','candidates':[]}
cases=[('compact32','estimate-compact32',[]),('compact16','estimate-compact16',[]),('compact-target16','estimate-compact16',['--target-horizontal'])]
for name,binary,flags in cases:
 cmd=[str(out/binary),'--fused-horizontal',*flags];dest=out/(name+'-validation.csv');log=out/(name+'-validation.stderr')
 with log.open('w') as f:subprocess.run(['/usr/bin/time','-l',*cmd,'-in','out/evaluation/validation.request.csv','-out',str(dest)],cwd=ROOT,stderr=f,check=True)
 with dest.open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
 assert len(p)==150053;item={'name':name,'score':score(y,p),'validation_rows':len(p),'same_as_v112':dest.read_bytes()==(ROOT/'out/v112/profile/validation.csv').read_bytes()};print(json.dumps(item),flush=True)
 item['validation_rss_bytes']=int(re.search(r'(\d+)\s+maximum resident set size',log.read_text())[1]);assert item['same_as_v112'];
 if item['score']>=99 and item['validation_rss_bytes']<=2000000000:
  speed=out/(name+'-1m.csv');speedlog=out/(name+'-1m.stderr')
  with speedlog.open('w') as f:subprocess.run(['/usr/bin/time','-l',*cmd,'-in','out/v99/speed1m.request.csv','-out',str(speed)],cwd=ROOT,stderr=f,check=True)
  text=speedlog.read_text();cpu=float(re.search('cpu_seconds=([0-9.]+)',text)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',text)[1]);item.update(cpu_seconds=cpu,init_seconds=init,query_seconds=cpu-init,estimated_billion_seconds=init+1000*(cpu-init),rss_bytes=int(re.search(r'(\d+)\s+maximum resident set size',text)[1]),output_sha256=hashlib.sha256(speed.read_bytes()).hexdigest(),runtime_file_bytes=(out/binary).stat().st_size+sum(q.stat().st_size for q in out.glob('*.bin')))
 report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V115-fast12-compact-pilot.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V115-fast12-compact-pilot.json').write_text(json.dumps(report,indent=2)+'\n')
