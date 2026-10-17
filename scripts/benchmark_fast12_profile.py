"""Full validation and two serial10m estimates of the same standard entry."""
import csv,hashlib,json,re,subprocess,argparse
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
parser=argparse.ArgumentParser();parser.add_argument('--version',default='115');a=parser.parse_args();folder=ROOT/f'out/phase-fast12-v{a.version}';out=ROOT/f'out/v{a.version}/profile';out.mkdir(parents=True,exist_ok=True);_,y,_,_=load('validation')
report={'state':'running','scope':'Apple M4/macOS local; actual10m repeated development requests with CSV I/O, init once; billion extrapolation, not official Linux','target_seconds':720,'validation_floor':99,'single_thread':True,'prediction_cache':False,'holdout_used':False,'runtime_file_bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file()),'runs':[]}
for name,input_path in [('validation','out/evaluation/validation.request.csv'),('speed10m-1','out/evaluation/speed10m-v45.request.csv'),('speed10m-2','out/evaluation/speed10m-v45.request.csv')]:
 dest=out/(name+'.csv');log=out/(name+'.stderr')
 with log.open('w') as f:subprocess.run(['/usr/bin/time','-l',str(folder/'estimate'),'-in',input_path,'-out',str(dest)],cwd=ROOT,stderr=f,check=True)
 text=log.read_text();cpu=float(re.search('cpu_seconds=([0-9.]+)',text)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',text)[1]);rows=int(re.search(r'rows=(\d+)',text)[1]);rss=int(re.search(r'(\d+)\s+maximum resident set size',text)[1]);h=hashlib.sha256()
 with dest.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 item={'name':name,'rows':rows,'cpu_seconds':cpu,'init_seconds':init,'query_seconds':cpu-init,'rss_bytes':rss,'output_sha256':h.hexdigest()}
 if name=='validation':
  with dest.open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
  assert len(p)==150053;item['score']=score(y,p);report['validation_score']=item['score'];item['matches_reference_candidate']=dest.read_bytes()==(ROOT/'out/v109/horizontal-source8-validation.csv').read_bytes();assert item['matches_reference_candidate']
 else:assert rows==10000000;item['billion_estimate_seconds']=init+100*(cpu-init)
 report['runs'].append(item);print(json.dumps(item),flush=True);(ROOT/f'reports/V{a.version}-fast12-profile.json').write_text(json.dumps(report,indent=2)+'\n')
report['runtime_file_bytes']=sum(p.stat().st_size for p in folder.iterdir() if p.is_file());report['state']='complete';speed=report['runs'][1:];report['peak_rss_bytes']=max(r['rss_bytes'] for r in report['runs']);report['speed_outputs_match']=speed[0]['output_sha256']==speed[1]['output_sha256'];report['goal_met']=report['validation_score']>=99 and all(r['billion_estimate_seconds']<=720 for r in speed) and report['runtime_file_bytes']<=100000000 and report['peak_rss_bytes']<=2000000000 and report['speed_outputs_match'];(ROOT/f'reports/V{a.version}-fast12-profile.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'goal_met':report['goal_met']}),flush=True)
