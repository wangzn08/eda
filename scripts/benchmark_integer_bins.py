"""Full parity and actual10m for64/256 tree wide layout, no holdout."""
import json,re,subprocess
from architecture import ROOT
import hashlib
provenance=json.loads((ROOT/'reports/V91-joint-patch-feasibility.json').read_text())
for asset,expected in provenance['baseline_assets'].items():
    assert hashlib.sha256((ROOT/'out/architecture-benchmark'/asset).read_bytes()).hexdigest()==expected, 'Joint baseline asset mismatch: '+asset
items=[]
base=['build/core_template_estimate','--buffered-output','--integer-bins','--joint-interaction','out/architecture-benchmark/joint-transient-xz6.bin','--corridor-geometry','--corridor-hubs','4','--model','out/architecture-benchmark/core-template-xz6.bin','--vertical-transients','out/architecture-benchmark/vertical-transients-xz.bin','--horizontal-transients','out/architecture-benchmark/horizontal-transients.bin','--far-vertical-delta','out/architecture-benchmark/vertical-distant-delta-xz6.bin','--wide-joint','--no-cache']
for trees in (64,):
 cmd=base+['--residual-model',f'out/v93/correction-{trees}.bin','--trees',str(trees)]
 out=ROOT/f'out/evaluation/validation.v97-integer-{trees}.csv'
 subprocess.run(cmd+['-in','out/evaluation/validation.request.csv','-out',str(out)],cwd=ROOT,capture_output=True,text=True,check=True)
 assert out.read_bytes()==(ROOT/f'out/evaluation/validation.v93-{trees}.csv').read_bytes()
 r=subprocess.run(['/usr/bin/time','-l']+cmd+['-in','out/evaluation/speed10m-v45.request.csv','-out','out/evaluation/speed10m-v97-budget.output.csv'],cwd=ROOT,capture_output=True,text=True,check=True)
 (ROOT/f'out/v93/v97-integer-speed-{trees}.log').write_text(r.stderr)
 rows=int(re.search(r'rows=(\d+)',r.stderr)[1]);assert rows==10000000
 cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1])
 files=[ROOT/'build/core_template_estimate']+[ROOT/'out/architecture-benchmark'/s for s in ('core-template-xz6.bin','vertical-transients-xz.bin','horizontal-transients.bin','vertical-distant-delta-xz6.bin','joint-transient-xz6.bin')]+[ROOT/f'out/v93/correction-{trees}.bin']
 scores=json.loads((ROOT/'reports/V93-joint-correction.json').read_text())['candidates'];score=next(s['cpp_score'] for s in scores if s['trees']==trees)
 items.append({'trees':trees,'validation_score':score,'full_validation_byte_exact':True,'rows':rows,'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':cpu-init,'requests_per_cpu_second':rows/(cpu-init),'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1]),'runtime_file_bytes':sum(f.stat().st_size for f in files)})
 print(items[-1],flush=True)
 (ROOT/'reports/V97-integer-throughput.json').write_text(json.dumps({'state':'running','candidates':items},indent=2)+'\n')
(ROOT/'reports/V97-integer-throughput.json').write_text(json.dumps({'state':'complete','candidates':items,'scope':'Actual10m repeated development requests with cache off, single runs; no final-billion, hidden-mix or officialLinux proof.'},indent=2)+'\n')
