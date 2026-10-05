"""Targeted port-composition pilot on fixed validation subset; no fitting."""
import csv,json,re,subprocess
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
x,y,_,_=load('validation');cross=(np.minimum(x[:,0],x[:,2])<76)&(np.maximum(x[:,0],x[:,2])>89)
m=cross&(x[:,1]//100==x[:,3]//100)&(x[:,1]%100<50)&(x[:,3]%100<50)
ids=np.flatnonzero(m);ids=ids[np.linspace(0,len(ids)-1,min(2048,len(ids)),dtype=int)]
folder=ROOT/'out/v90';folder.mkdir(exist_ok=True);request=folder/'pilot.request.csv'
with (ROOT/'out/evaluation/validation.request.csv').open() as f:rows=list(csv.reader(f))
with request.open('w') as f:w=csv.writer(f);w.writerow(rows[0]);w.writerows(rows[i+1] for i in ids)
items=[]
for count in (0,4,16,32):
 out=folder/f'pilot-{count}.csv'
 cmd=['build/core_template_estimate','--model','out/architecture-benchmark/core-template-xz6.bin','--vertical-transients','out/architecture-benchmark/vertical-transients-xz.bin','--horizontal-transients','out/architecture-benchmark/horizontal-transients.bin','--far-vertical-delta','out/architecture-benchmark/vertical-distant-delta-xz6.bin','--corridor-geometry','--no-cache','-in',str(request),'-out',str(out)]
 if count:cmd+=['--corridor-hubs',str(count)]
 r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);(folder/f'pilot-{count}.log').write_text(r.stderr)
 with out.open() as f:p=np.array([int(row['delay']) for row in csv.DictReader(f)])
 cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1])
 items.append({'hubs':count,'rows':len(ids),'pilot_score':score(y[ids],p),'mean_absolute_error_ps':float(np.abs(p-y[ids]).mean()),'mean_signed_error_ps':float((p-y[ids]).mean()),'query_cpu_seconds':cpu-init});print(items[-1],flush=True)
r={'split':'validation','holdout_used':False,'residual_model':False,'selection':'Fixed evenly spaced2048 same-band block-crossing rows','candidates':items,'scope':'Targeted approximate min-plus composition pilot, no full validation, actual path certificate or final throughput claim.'}
(ROOT/'reports/V90-corridor-hub-pilot.json').write_text(json.dumps(r,indent=2)+'\n')
