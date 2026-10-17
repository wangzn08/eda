"""V103 remove learned head and compare corridor/compiled layouts under new >=99 floor."""
import csv,json,re,subprocess
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v103';out.mkdir(exist_ok=True);_,y,_,_=load('validation')
base=['build/core_template_estimate','--buffered-output','--model','out/architecture-benchmark/core-template-xz6.bin','--vertical-transients','out/architecture-benchmark/vertical-transients-xz.bin','--horizontal-transients','out/architecture-benchmark/horizontal-transients.bin','--far-vertical-delta','out/architecture-benchmark/vertical-distant-delta-xz6.bin','--joint-interaction','out/architecture-benchmark/joint-transient-xz6.bin','--corridor-geometry','--no-cache']
report={'holdout_used':False,'scope':'Actual1m pilot, full validation, raw architecture heads; no final-billion proof','candidates':[]}
for name,flags in [('wide-hubs4',['--wide-joint','--corridor-hubs','4']),('wide-hubs0',['--wide-joint']),('scalar-hubs0',[]),('wide-hubs1',['--wide-joint','--corridor-hubs','1'])]:
 cmd=base+flags;dest=out/(name+'.csv');subprocess.run(cmd+['-in','out/evaluation/validation.request.csv','-out',str(dest)],cwd=ROOT,capture_output=True,text=True,check=True)
 with dest.open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
 np.save(out/(name+'.npy'),p)
 r=subprocess.run(['/usr/bin/time','-l']+cmd+['-in','out/v99/speed1m.request.csv','-out',str(out/'speed.output.csv')],cwd=ROOT,capture_output=True,text=True,check=True)
 cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1]);rows=int(re.search('rows=(\d+)',r.stderr)[1]);assert rows==1000000
 item={'name':name,'score':score(y,p),'rows':rows,'cpu_seconds':cpu,'init_cpu_seconds':init,'query_cpu_seconds':cpu-init,'rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1]),'billion_estimate_seconds':init+1000*(cpu-init)};report['candidates'].append(item);print(json.dumps(item),flush=True)
 (ROOT/'reports/V103-template-latency.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V103-template-latency.json').write_text(json.dumps(report,indent=2)+'\n')
