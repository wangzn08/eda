"""Full validation of architecture-only finite-distance growth correction."""
import csv,json,re,subprocess
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
_,y,_,_=load('validation');items=[]
for cap in (0,2,4,4294967295):
    name=f'v77-cap{cap}';out=ROOT/f'out/evaluation/validation.{name}.csv'
    cmd=['/usr/bin/time','-l','build/core_template_estimate','--model','out/architecture-benchmark/core-template-zlib.bin','--vertical-transients','out/architecture-benchmark/vertical-transients.bin','--growth-cap',str(cap),'-in','out/evaluation/validation.request.csv','-out',str(out),'--no-cache']
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);(ROOT/f'out/{name}.log').write_text(r.stderr)
    with out.open() as f:p=np.array([int(a['delay']) for a in csv.DictReader(f)],dtype=np.float64)
    assert len(p)==len(y)
    cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1])
    item={'growth_cap':cap,'validation_score':score(y,p),'exact_fraction':float(np.mean(p==y)),
          'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':cpu-init,
          'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1])};items.append(item);print(item,flush=True)
report={'rows':len(y),'holdout_used':False,'golden_labels_used_for_asset':False,'baseline_template_score':96.34999162187053,'candidates':items,
        'scope':'C++ full validation, no learned correction. Research assets exceed100MB together; not submission profile or billion acceptance.'}
(ROOT/'reports/V77-vertical-transient-validation.json').write_text(json.dumps(report,indent=2)+'\n')
