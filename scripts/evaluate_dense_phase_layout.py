"""Alternating paired precision-search benchmark; no request-result cache."""
import hashlib,json,re,subprocess
from architecture import ROOT
report={'rows':1001,'holdout_used':False,'runs':[],'scope':'Fixed validation pilot, same certified search and .00024 bound. Timing is actual pilot CPU; no billion extrapolation or official acceptance.'}
for repetition in range(3):
    for dense in (False,True):
        name=f'v72-{int(dense)}-{repetition}';out=ROOT/f'out/evaluation/{name}.csv';bounds=ROOT/f'out/evaluation/{name}.bounds.csv'
        cmd=['/usr/bin/time','-l','build/phase_estimate','-in','out/evaluation/v72-pilot.request.csv','-out',str(out),'--phase-bounds','models/phase-bounds-safe.bin','--cycle-oracle','out/phase-precision-v40/long-tail.bin','--no-cache','--certificate',str(bounds)]
        if dense:cmd.append('--dense-phase')
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);(ROOT/f'out/{name}.log').write_text(r.stderr)
        cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1])
        report['runs'].append({'dense_layout':dense,'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':cpu-init,
          'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1]),
          'prediction_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'certificate_sha256':hashlib.sha256(bounds.read_bytes()).hexdigest()})
report['identical_predictions']=len({r['prediction_sha256'] for r in report['runs']})==1
report['identical_certificates']=len({r['certificate_sha256'] for r in report['runs']})==1
(ROOT/'reports/V72-dense-phase-layout.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
