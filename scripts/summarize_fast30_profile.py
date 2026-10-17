"""Read completed actual10m logs, score full validation, check artifact and parity."""
import csv,hashlib,json,re
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
folder=ROOT/'out/v108/profile';profile=ROOT/'out/phase-fast30-v108';_,y,_,_=load('validation')
with (folder/'validation.csv').open() as f:p=np.array([int(r['delay']) for r in csv.DictReader(f)])
assert len(p)==150053;validation_score=score(y,p)
assert (folder/'validation.csv').read_bytes()==(ROOT/'out/v105/validation.csv').read_bytes()
assert (folder/'retained-validation.csv').read_bytes()==(ROOT/'out/evaluation/validation.v93-64.csv').read_bytes()
manifest=json.loads((profile/'manifest.json').read_text());files={}
for name,expected in manifest['files'].items():
 path=profile/name;digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==expected['sha256'];files[name]=path.stat().st_size
runtime_bytes=sum(files.values());directory_bytes=sum(p.stat().st_size for p in profile.iterdir() if p.is_file())
items=[]
for name in ['speed10m-1','control-speed10m','speed10m-2']:
 text=(folder/(name+'.stderr')).read_text();match=re.search(r'rows=(\d+) cpu_seconds=([0-9.]+) initialization_seconds=([0-9.]+)',text);assert match,name
 rows,cpu,init=int(match[1]),float(match[2]),float(match[3]);assert rows==10000000
 rss=int(re.search(r'(\d+)\s+maximum resident set size',text)[1]);query=cpu-init
 items.append({'name':name,'layout':'source-major-control' if name.startswith('control') else 'phase-major','rows':rows,'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':query,'query_cpu_seconds_per_million':query/10,'rss_bytes':rss,'estimated_billion_cpu_seconds':init+100*query,'estimated_billion_cpu_minutes':(init+100*query)/60})
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
output_hashes={name:sha(folder/(name+'.csv')) for name in ['speed10m-1','control-speed10m','speed10m-2']};assert len(set(output_hashes.values()))==1,'Whole10m outputs differ'
chosen=[a for a in items if a['layout']=='phase-major'];complete=validation_score>=99 and directory_bytes<=100000000 and max(a['rss_bytes'] for a in chosen)<=2000000000 and max(a['estimated_billion_cpu_seconds'] for a in chosen)<=1800
report={'state':'complete' if complete else 'target-not-met','validation_rows':len(p),'validation_score':validation_score,'validation_byte_exact_to_v105':True,'retained_v93_validation_byte_exact':True,'machine':{'cpu':'Apple M4','os':'macOS 27.0.1'},'runtime_file_bytes':runtime_bytes,'profile_directory_bytes':directory_bytes,'files':files,'runs':items,'speed_output_sha256':output_hashes,'whole10m_outputs_byte_exact':True,'holdout_used':False,'prediction_cache':False,'estimated_billion_cpu_minutes_mean':float(np.mean([a['estimated_billion_cpu_minutes'] for a in chosen])),'estimated_billion_cpu_minutes_worst':max(a['estimated_billion_cpu_minutes'] for a in chosen),'scope':'Local macOS single-thread actual10m CPU, validation >=99 and billion-time extrapolation <=30 minutes; same development-derived repeated mix and stable-throughput assumption, not officialLinux acceptance or actual-billion proof'}
(ROOT/'reports/V108-fast30-profile.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert complete,'Continue optimization'
