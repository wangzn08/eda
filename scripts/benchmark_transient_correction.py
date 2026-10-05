"""Actual10m CSV throughput for new transient profiles; no cache, no billion claim."""
import json,re,subprocess,time
from architecture import ROOT
items=[]
for trees in (64,128,256):
    log=ROOT/f'out/v79/speed10m-{trees}.log';output=ROOT/'out/evaluation/speed10m-v79.output.csv'
    cmd=['/usr/bin/time','-l','build/core_template_estimate','--model','out/architecture-benchmark/core-template-xz.bin','--vertical-transients','out/architecture-benchmark/vertical-transients.bin','--residual-model',f'out/v79/correction-{trees}.bin','--trees',str(trees),'-in','out/evaluation/speed10m-v45.request.csv','-out',str(output),'--no-cache']
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);log.write_text(r.stderr)
    cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1]);rows=int(re.search(r'rows=(\d+)',r.stderr)[1])
    assert rows==10000000
    files=[ROOT/'build/core_template_estimate',ROOT/'out/architecture-benchmark/core-template-xz.bin',ROOT/'out/architecture-benchmark/vertical-transients.bin',ROOT/f'out/v79/correction-{trees}.bin']
    items.append({'trees':trees,'rows':rows,'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':cpu-init,'requests_per_cpu_second':rows/(cpu-init),'runtime_file_bytes':sum(f.stat().st_size for f in files),'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1])});print(items[-1],flush=True)
    (ROOT/'reports/V79-transient-throughput.json').write_text(json.dumps({'state':'running','candidates':items},indent=2)+'\n')
report={'state':'complete','candidates':items,'scope':'10m repeated development requests, every row computed with prediction cache disabled, single runs. Actual CPU includes CSV input/output; no full billion proof, arbitrary hidden mix guarantee or official acceptance.'}
(ROOT/'reports/V79-transient-throughput.json').write_text(json.dumps(report,indent=2)+'\n')
