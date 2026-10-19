"""Full native validation plus existing disjoint novel-request timing inputs."""
import argparse,csv,hashlib,json,re,subprocess,time
from pathlib import Path
import numpy as np
from architecture import ROOT
from native_research_labels import load_labels
from experiment_v7_teacher import score
from selected_physics_interactions import augment

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
 return h.hexdigest()

p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--directory',required=True);p.add_argument('--expected-predictions',required=True);p.add_argument('--speed-runs',type=int,choices=(1,2),default=2);p.add_argument('--check-physics-features',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args()
folder=ROOT/a.directory;out=ROOT/f'out/v{a.version}/score-profile';out.mkdir(parents=True,exist_ok=True)
report_path=ROOT/f'reports/V{a.version}-native-score-profile.json'
inventory=json.loads((ROOT/'reports/V242-novel-request-profile.json').read_text())['input_inventory']
before={p.name:digest(p) for p in folder.iterdir() if p.is_file()}
manifest=json.loads((ROOT/f'out/v{a.version}/runtime-manifest.json').read_text())
assert before=={name:v['sha256'] for name,v in manifest['files'].items()}
report={'state':'running','version':a.version,'scope':'Apple M4/macOS, standard CSV CLI, native full validation then two disjoint synthetic novel-request inputs; extrapolation not official hidden input measurement','architecture_operator_cache':False,'prediction_cache':False,'holdout_used':False,'runtime_file_bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file()),'asset_sha256_before':before,'runs':[],'fit_manifest':manifest,'novel_input_inventory':inventory}
if a.resume:
 previous=json.loads(report_path.read_text());assert previous['asset_sha256_before']==before and previous['fit_manifest']==manifest and previous['novel_input_inventory']==inventory
 for item in previous['runs']:assert digest(out/f"{item['name']}.csv")==item['output_sha256']
 report=previous;report['state']='running'
def save():report_path.write_text(json.dumps(report,indent=2)+'\n')
save();z=load_labels();yv=z['yv'];n=len(z['y'])
cases=[('validation',ROOT/'out/evaluation/validation.request.csv',150053)]+[(f'novel-{i+1}',ROOT/v['path'],v['rows']) for i,v in enumerate(inventory['files'][:a.speed_runs])]
for name,source,expected_rows in cases:
 if any(item['name']==name for item in report['runs']):continue
 if name!='validation':assert digest(source)==inventory['files'][int(name[-1])-1]['sha256']
 dest=out/f'{name}.csv';log=out/f'{name}.stderr';command=[str(folder/'estimate'),'-in',str(source),'-out',str(dest)]
 if name=='validation' and a.check_physics_features:command+=['--feature-out',str(out/'validation.features.f32')]
 start=time.monotonic()
 with log.open('w') as f:
  process=subprocess.Popen(['/usr/bin/time','-l',*command],cwd=ROOT,stderr=f)
  if name=='validation':
   time.sleep(.3)
   for row in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
    fields=row.strip().split(None,2)
    if len(fields)==3 and fields[1]==str(process.pid) and fields[2].split()[0]==str(folder/'estimate'):
     snapshot=subprocess.check_output(['ps','-M','-p',fields[0]],text=True);assert len(snapshot.strip().splitlines())==2
     (out/'single-thread-snapshot.txt').write_text(snapshot);report['observed_runtime_threads']=1;break
   assert report.get('observed_runtime_threads')==1
  assert process.wait()==0,log.read_text()
 wall=time.monotonic()-start;text=log.read_text();cpu=float(re.search(r'cpu_seconds=([0-9.]+)',text)[1]);init=float(re.search(r'initialization_seconds=([0-9.]+)',text)[1]);rows=int(re.search(r'rows=(\d+)',text)[1]);assert rows==expected_rows
 assert 'architecture_operator_cache_bytes=' not in text
 item={'name':name,'rows':rows,'total_cpu_seconds':cpu,'initialization_cpu_seconds':init,'query_cpu_seconds':cpu-init,'total_wall_seconds':wall,'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',text)[1]),'output_sha256':digest(dest)}
 values=[]
 with source.open() as inputs,dest.open() as outputs:
  for source_row,result in zip(csv.DictReader(inputs),csv.DictReader(outputs),strict=True):
   assert (source_row['From'],source_row['To'])==(result['From'],result['To'])
   value=int(result['delay']);assert 0<=value<1000000000
   if name=='validation':values.append(value)
 item['output_pin_order_and_range_verified']=True
 if name=='validation':
  values=np.array(values);assert len(values)==expected_rows;item['score']=score(yv,values);report['validation_score']=item['score'];item['all_predictions_equal_offline']=bool(np.array_equal(values,np.load(ROOT/a.expected_predictions)));assert item['all_predictions_equal_offline']
  if a.check_physics_features:
   native=np.memmap(out/'validation.features.f32',mode='r',dtype='<f4',shape=(expected_rows,manifest['features']))
   original=np.memmap(ROOT/'out/v243/all.features.f32',mode='r',dtype='<f4',shape=(n+expected_rows,137))[n:]
   item['all_native_feature_elements_equal_python']=bool(np.array_equal(native,augment(original)));assert item['all_native_feature_elements_equal_python']
 else:
  item['query_cpu_seconds_per_request']=(cpu-init)/rows;item['billion_estimate_cpu_seconds']=init+(cpu-init)/rows*1e9
 report['runs'].append(item);save();print(json.dumps(item),flush=True)
after={p.name:digest(p) for p in folder.iterdir() if p.is_file()};assert after==before;report['asset_sha256_after']=after;report['state']='complete' if len(report['runs'])==3 else 'complete-single-speed-screen';report['peak_rss_bytes']=max(r['maximum_rss_bytes'] for r in report['runs']);speed=report['runs'][1:];report['pooled_query_cpu_seconds_per_request']=sum(r['query_cpu_seconds'] for r in speed)/sum(r['rows'] for r in speed);report['pooled_billion_estimate_cpu_seconds']=sum(r['initialization_cpu_seconds'] for r in speed)/len(speed)+report['pooled_query_cpu_seconds_per_request']*1e9;save()
print(json.dumps({'score':report['validation_score'],'billion_seconds':report['pooled_billion_estimate_cpu_seconds'],'rss':report['peak_rss_bytes']}),flush=True)
