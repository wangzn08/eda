"""Full validation of separate/coupled architecture transient corrections."""
import csv,json,re,subprocess
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
_,y,_,_=load('validation');items=[]
for use_vertical in (False,True):
    name=f'v81-{int(use_vertical)}';out=ROOT/f'out/evaluation/validation.{name}.csv'
    cmd=['/usr/bin/time','-l','build/core_template_estimate','--model','out/architecture-benchmark/core-template-xz.bin','--horizontal-transients','out/architecture-benchmark/horizontal-transients.bin','-in','out/evaluation/validation.request.csv','-out',str(out),'--no-cache']
    if use_vertical:cmd+=['--vertical-transients','out/architecture-benchmark/vertical-transients-xz.bin']
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);(ROOT/f'out/{name}.log').write_text(r.stderr)
    with out.open() as f:p=np.array([int(a['delay']) for a in csv.DictReader(f)],dtype=np.float64)
    assert len(p)==len(y)
    cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1])
    item={'vertical_enabled':use_vertical,'horizontal_enabled':True,'validation_score':score(y,p),'exact_fraction':float(np.mean(p==y)),'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':cpu-init,'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1])};items.append(item);print(item,flush=True)
r={'rows':len(y),'holdout_used':False,'golden_labels_used_for_assets':False,'template_baseline_score':96.34999162187053,'vertical_baseline_score':97.97144301878541,'candidates':items,'scope':'Unlearned nominal transient corrections; complete validation, single CPU measurements; not physical path certificate, no hidden/billion acceptance.'}
(ROOT/'reports/V81-horizontal-coupling.json').write_text(json.dumps(r,indent=2)+'\n')
