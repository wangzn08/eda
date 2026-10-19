"""Paired native validation and novel throughput under a hard 600 CPU s budget."""
import argparse,csv,hashlib,json,re,subprocess,time
from pathlib import Path
import numpy as np
from architecture import ROOT
from native_research_labels import load_labels

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--expected');p.add_argument('--speed-runs',type=int,choices=(1,2),default=2);p.add_argument('--resume',action='store_true');a=p.parse_args()
 work=ROOT/f'out/v{a.version}';folder=ROOT/f'out/runtime-budget-v{a.version}';out=work/'budget-profile';out.mkdir(exist_ok=True)
 path=ROOT/f'reports/V{a.version}-budget-profile.json';assets={p.name:digest(p) for p in folder.iterdir() if p.is_file()};manifest=json.loads((work/'runtime-manifest.json').read_text())
 assert assets=={k:v['sha256'] for k,v in manifest['files'].items()}
 report={'state':'running','version':a.version,'scope':'Apple M4/macOS single process and single thread standard CSV CLI; two disjoint synthetic novel-request batches; billion extrapolation includes one initialization, not an official judge measurement','target_cpu_seconds':600,'prediction_cache':False,'architecture_operator_cache':False,'holdout_used':False,'asset_sha256_before':assets,'runtime_bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file()),'runs':[]}
 if a.resume and path.exists():
  report=json.loads(path.read_text());assert report['asset_sha256_before']==assets
 inventory=json.loads((ROOT/'reports/V242-novel-request-profile.json').read_text())['input_inventory'];report['fixed_novel_input_inventory']=inventory
 labels=load_labels();yv=labels['yv'];expected=np.load(ROOT/a.expected) if a.expected else None
 cases=[('validation',ROOT/'out/evaluation/validation.request.csv',len(yv))]+[(f'novel-{i}',ROOT/f'out/v242/novel-requests/novel-{i}.request.csv',3000000) for i in range(1,a.speed_runs+1)]
 for name,inp,n in cases:
  old=next((r for r in report['runs'] if r['name']==name),None)
  output=out/f'{name}.csv';err=out/f'{name}.stderr'
  if old:
   assert digest(output)==old['output_sha256'];continue
  input_sha=digest(inp)
  if name.startswith('novel-'):
   item_inventory=next(x for x in inventory['files'] if Path(x['path']).name==inp.name);assert input_sha==item_inventory['sha256']
  start=time.monotonic()
  with err.open('w') as log:
   process=subprocess.Popen(['/usr/bin/time','-l',str(folder/'estimate'),'-in',str(inp),'-out',str(output)],stderr=log,cwd=ROOT)
   time.sleep(.15)
   child=subprocess.run(['pgrep','-P',str(process.pid)],capture_output=True,text=True)
   observed_threads=None
   if child.returncode==0:
    ids=child.stdout.split()
    if len(ids)==1:
     snapshot=subprocess.run(['ps','-M','-p',ids[0]],capture_output=True,text=True)
     (out/f'{name}.threads.txt').write_text(snapshot.stdout)
     observed_threads=max(0,len(snapshot.stdout.strip().splitlines())-1)
   assert process.wait()==0
   if observed_threads is not None:assert observed_threads==1

  wall=time.monotonic()-start;s=err.read_text();m=re.search(r'rows=(\d+) cpu_seconds=([\d.]+) initialization_seconds=([\d.]+)',s);assert m and int(m[1])==n
  cpu,init=map(float,m.groups()[1:]);rss=int(re.search(r'(\d+)\s+maximum resident set size',s)[1]);query=cpu-init
  pred=[];count=0
  with inp.open() as f,output.open() as g:
   for x,y in zip(csv.DictReader(f),csv.DictReader(g),strict=True):
    assert x['From']==y['From'] and x['To']==y['To'];v=int(y['delay']);assert 0<=v<10**9
    if name=='validation':pred.append(v)
    count+=1
  assert count==n and digest(inp)==input_sha
  item={'name':name,'rows':n,'input_sha256':input_sha,'total_cpu_seconds':cpu,'initialization_cpu_seconds':init,'query_cpu_seconds':query,'wall_seconds':wall,'maximum_rss_bytes':rss,'output_sha256':digest(output),'output_pin_order_and_range_verified':True,'observed_runtime_threads':observed_threads}
  if name=='validation':
   pred=np.array(pred);item['score']=float(100*np.mean(1-np.tanh(4*abs(pred-yv)/np.maximum(yv,1))))
   if expected is not None:assert np.array_equal(pred,expected);item['all_predictions_equal_offline']=True
  else:item.update(query_cpu_seconds_per_request=query/n,billion_estimate_cpu_seconds=init+query/n*10**9)
  report['runs'].append(item);print(json.dumps(item),flush=True);path.write_text(json.dumps(report,indent=2)+'\n')
 report['asset_sha256_after']={p.name:digest(p) for p in folder.iterdir() if p.is_file()};assert report['asset_sha256_after']==assets
 speeds=[r for r in report['runs'] if r['name'].startswith('novel-')];report['validation_score']=report['runs'][0]['score'];report['peak_rss_bytes']=max(r['maximum_rss_bytes'] for r in report['runs']);report['pooled_billion_estimate_cpu_seconds']=sum(r['billion_estimate_cpu_seconds'] for r in speeds)/len(speeds);report['all_measured_speed_runs_under_budget']=all(r['billion_estimate_cpu_seconds']<=600 for r in speeds)
 report['state']='complete' if len(speeds)==2 else 'complete-single-speed-screen';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['state','validation_score','pooled_billion_estimate_cpu_seconds','all_measured_speed_runs_under_budget','peak_rss_bytes']}),flush=True)
if __name__=='__main__':main()
