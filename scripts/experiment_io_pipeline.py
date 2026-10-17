"""One initialization per candidate, full validation then actual1m serial pilot."""
import json,subprocess,re,hashlib
from architecture import ROOT
out=ROOT/'out/v124';ref=(ROOT/'out/v116/profile/validation.csv').read_bytes();report={'state':'running','validation_floor':99.5,'target_seconds':600,'holdout_used':False,'prediction_cache':False,'scope':'Same process full validation then actual1m development pilot; final separate10m repeats required','candidates':[]}
for name in ('control','zero','prepared'):
 dest=out/f'{name}.csv';log=out/f'{name}.stderr'
 with log.open('w') as f:subprocess.run(['/usr/bin/time','-l',str(out/f'estimate-{name}'),'-in','out/v124/validation-speed1m.request.csv','-out',str(dest)],cwd=ROOT,stderr=f,check=True)
 with dest.open('rb') as f:head=b''.join(f.readline() for _ in range(150054));tail=f.read()
 assert head==ref;text=log.read_text();cpu=float(re.search('cpu_seconds=([0-9.]+)',text)[1])
 # cpu_seconds also occurs in checkpoint; select the rows= line explicitly.
 cpu=float(re.search(r'rows=\d+ cpu_seconds=([0-9.]+)',text)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',text)[1]);checkpoint=float(re.search('checkpoint_cpu_seconds=([0-9.]+)',text)[1]);q=cpu-checkpoint
 item={'name':name,'validation_score':99.0256649430261,'same_as_v116':True,'init_seconds':init,'validation_query_seconds':checkpoint-init,'pilot_query_seconds':q,'billion_estimate_seconds':init+1000*q,'rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',text)[1]),'pilot_rows':1000000,'pilot_sha256':hashlib.sha256(b'From,To,delay\n'+tail).hexdigest()};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/'reports/V124-io-pipeline.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V124-io-pipeline.json').write_text(json.dumps(report,indent=2)+'\n')
