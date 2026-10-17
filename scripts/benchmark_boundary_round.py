"""V99 boundary model parity and same-binary paired 1m CPU measurements."""
import csv,itertools,json,re,subprocess
import numpy as np
from catboost import CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
out=ROOT/'out/v99'
for depth,nt in ((8,256),(10,64),(10,128)):
 m=CatBoostRegressor();m.load_model(str(out/f'boundary-{depth}.cbm'));p=out/f'boundary-{depth}.json';m.save_model(str(p),format='json')
 subprocess.run([str(ROOT/'out/research-env/bin/python'),'scripts/export_fast_residual.py',str(p),str(out/f'boundary-d{depth}-t{nt}.bin'),'--trees',str(nt),'--boundary'],cwd=ROOT,check=True)
for nt in (64,128,256,512):
 subprocess.run([str(ROOT/'out/research-env/bin/python'),'scripts/export_asymmetric_boundary.py','out/v100/boundary-127.txt',f'out/v100/asymmetric-{nt}.bin','--trees',str(nt)],cwd=ROOT,check=True)
 np.save(out/f'asymmetric-{nt}.npy',np.load(ROOT/f'out/v100/l127-t{nt}.npy'))
base=['build/core_template_estimate','--buffered-output','--integer-bins','--joint-interaction','out/architecture-benchmark/joint-transient-xz6.bin','--corridor-geometry','--corridor-hubs','4','--model','out/architecture-benchmark/core-template-xz6.bin','--vertical-transients','out/architecture-benchmark/vertical-transients-xz.bin','--horizontal-transients','out/architecture-benchmark/horizontal-transients.bin','--far-vertical-delta','out/architecture-benchmark/vertical-distant-delta-xz6.bin','--wide-joint','--no-cache']
report={'holdout_used':False,'scope':'Full validation parity and paired actual 1m repeated requests; no billion proof','validation':[],'timings':[]}
_,yv,_,_=load('validation')
for name,nt,asset in [('retained-v93-64',64,'out/v93/correction-64.bin'),('boundary-d8-t256',256,'out/v99/boundary-d8-t256.bin'),('boundary-d10-t64',64,'out/v99/boundary-d10-t64.bin'),('boundary-d10-t128',128,'out/v99/boundary-d10-t128.bin')]+[(f'asymmetric-{nt}',nt,f'out/v100/asymmetric-{nt}.bin') for nt in (64,128,256,512)]:
 dest=out/(name+'.csv');r=subprocess.run(base+['--residual-model',asset,'--trees',str(nt),'-in','out/evaluation/validation.request.csv','-out',str(dest)],cwd=ROOT,capture_output=True,text=True,check=True)
 with dest.open() as f:p=np.array([int(t['delay']) for t in csv.DictReader(f)])
 expected=np.load(out/(name+'.npy'));mismatch=int(np.sum(p!=expected));maxdiff=int(np.max(np.abs(p-expected)));assert maxdiff<=1,(name,mismatch,maxdiff)
 files=[ROOT/'build/core_template_estimate',ROOT/asset]+[ROOT/'out/architecture-benchmark'/s for s in ['core-template-xz6.bin','vertical-transients-xz.bin','horizontal-transients.bin','vertical-distant-delta-xz6.bin','joint-transient-xz6.bin']]
 report['validation'].append({'name':name,'cpp_score':score(yv,p),'python_mismatches':mismatch,'max_abs_python_difference_ps':maxdiff,'runtime_file_bytes':sum(f.stat().st_size for f in files)});print(report['validation'][-1],flush=True)
 (ROOT/'reports/V99-boundary-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
request=out/'speed1m.request.csv'
with (ROOT/'out/evaluation/speed10m-v45.request.csv').open() as f,request.open('w') as g:g.writelines(itertools.islice(f,1000001))
for name in ['boundary-d10-t64','retained-v93-64','asymmetric-128','asymmetric-64','asymmetric-64','asymmetric-128','retained-v93-64','boundary-d10-t64']:
 asset='out/v93/correction-64.bin' if name=='retained-v93-64' else f'out/v100/{name}.bin' if name.startswith('asymmetric') else 'out/v99/boundary-d10-t64.bin'
 nt=int(name.split('-')[-1]) if name.startswith('asymmetric') else 64
 r=subprocess.run(['/usr/bin/time','-l']+base+['--residual-model',asset,'--trees',str(nt),'-in',str(request),'-out',str(out/'speed.output.csv')],cwd=ROOT,capture_output=True,text=True,check=True)
 cpu=float(re.search(r'cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search(r'initialization_seconds=([0-9.]+)',r.stderr)[1]);rows=int(re.search(r'rows=(\d+)',r.stderr)[1]);assert rows==1000000
 report['timings'].append({'name':name,'rows':rows,'cpu_seconds':cpu,'init_cpu_seconds':init,'query_cpu_seconds':cpu-init,'rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1])});print(report['timings'][-1],flush=True)
 (ROOT/'reports/V99-boundary-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
report['summary']=[]
for name in dict.fromkeys(t['name'] for t in report['timings']):
 runs=[t for t in report['timings'] if t['name']==name];mean=sum(t['query_cpu_seconds'] for t in runs)/len(runs);init=sum(t['init_cpu_seconds'] for t in runs)/len(runs)
 report['summary'].append({'name':name,'mean_query_cpu_seconds_per_million':mean,'measured_runs':len(runs),'billion_estimate_seconds':init+1000*mean,'assumption':'Same request mix, unchanged throughput, initialization once; extrapolation only'})
report['state']='complete';(ROOT/'reports/V99-boundary-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
