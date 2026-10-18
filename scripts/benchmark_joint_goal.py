"""Full validation and two serial10m estimates of the same standard entry."""
import csv,hashlib,json,re,subprocess,argparse,time
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
parser=argparse.ArgumentParser();parser.add_argument('--version',required=True);parser.add_argument('--directory',required=True);parser.add_argument('--operator-cache',action='store_true');parser.add_argument('--speed-runs',type=int,choices=[1,2],default=2);a=parser.parse_args();folder=ROOT/a.directory;out=ROOT/f'out/v{a.version}/joint-profile';out.mkdir(parents=True,exist_ok=True);_,y,_,_=load('validation')
assets={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob("*") if p.is_file()};assert 'estimate' in assets
report={'asset_sha256_before':assets,'state':'running','scope':'Apple M4/macOS local; actual10m repeated development requests with CSV I/O, init once; billion extrapolation, not official Linux','target_seconds':600,'validation_floor':99.5,'single_thread':True,'prediction_cache':False,'architecture_operator_cache':a.operator_cache,'holdout_used':False,'runtime_file_bytes':sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()),'runs':[]}
for name,input_path in [('validation','out/evaluation/validation.request.csv')]+[(f'speed10m-{i+1}','out/evaluation/speed10m-v45.request.csv') for i in range(a.speed_runs)]:
 dest=out/(name+'.csv');log=out/(name+'.stderr')
 with log.open('w') as f:
  process=subprocess.Popen(['/usr/bin/time','-l',str(folder/'estimate'),'-in',input_path,'-out',str(dest)],cwd=ROOT,stderr=f)
  # Observe the actual runtime child; the Python monitor is outside its CPU/RSS.
  if name=='validation':
   captured=False
   for attempt in range(4):
    time.sleep(.25)
    for row in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
     fields=row.strip().split(None,2)
     if len(fields)==3 and fields[1]==str(process.pid) and fields[2].split()[0]==str(folder/'estimate'):
      snapshot=subprocess.check_output(['ps','-M','-p',fields[0]],text=True)
      assert len(snapshot.strip().splitlines())==2
      (ROOT/f'out/v{a.version}/single-thread-snapshot.txt').write_text(snapshot)
      (ROOT/f'out/v{a.version}/single-thread-snapshot.provenance.json').write_text(json.dumps({'method':'ps -M','runtime_pid':int(fields[0]),'observed_threads':1,'source':'Live validation runtime child'})+'\n')
      captured=True;break
    if captured:break
   assert captured,'Could not observe runtime thread count'
  assert process.wait()==0,'Runtime failed' 
 text=log.read_text();cpu=float(re.search('cpu_seconds=([0-9.]+)',text)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',text)[1]);rows=int(re.search(r'rows=(\d+)',text)[1]);rss=int(re.search(r'(\d+)\s+maximum resident set size',text)[1]);h=hashlib.sha256()
 with dest.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 item={'name':name,'rows':rows,'cpu_seconds':cpu,'init_seconds':init,'query_seconds':cpu-init,'rss_bytes':rss,'output_sha256':h.hexdigest()}
 operator_match=re.search(r'architecture_operator_cache_bytes=(\d+) hits=(\d+) misses=(\d+) final_prediction_cache=0',text)
 assert bool(operator_match)==a.operator_cache
 if operator_match:item['architecture_operator_cache']={'bytes':int(operator_match[1]),'hits':int(operator_match[2]),'misses':int(operator_match[3]),'final_prediction_cache':False}
 if name=='validation':
  with dest.open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
  assert len(p)==150053;item['score']=score(y,p);report['validation_score']=item['score'];item['scope']='Full validation of this candidate; differing from V116 is allowed'
 else:assert rows==10000000;item['billion_estimate_seconds']=init+100*(cpu-init)
 report['runs'].append(item);print(json.dumps(item),flush=True);(ROOT/f'reports/V{a.version}-joint-goal-profile.json').write_text(json.dumps(report,indent=2)+'\n')
after={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob("*") if p.is_file()};assert after==assets;report['asset_sha256_after']=after
report['runtime_file_bytes']=sum(p.stat().st_size for p in folder.rglob("*") if p.is_file());report['state']='complete' if a.speed_runs==2 else 'complete-single-speed-screen';speed=report['runs'][1:];report['peak_rss_bytes']=max(r['rss_bytes'] for r in report['runs']);report['speed_outputs_match']=(speed[0]['output_sha256']==speed[1]['output_sha256']) if len(speed)==2 else None;report['goal_met']=len(speed)==2 and report['validation_score']>=99.5 and all(r['billion_estimate_seconds']<=600 for r in speed) and report['runtime_file_bytes']<=100000000 and report['peak_rss_bytes']<=2000000000 and report['speed_outputs_match'];(ROOT/f'reports/V{a.version}-joint-goal-profile.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'goal_met':report['goal_met']}),flush=True)
