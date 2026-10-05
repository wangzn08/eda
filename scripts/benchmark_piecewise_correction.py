"""Actual10m CSV throughput for new transient profiles; no cache, no billion claim."""
import json,re,subprocess,time
from architecture import ROOT
import csv
from architecture_benchmark_data import load
from experiment_v7_teacher import score
import numpy as np
validation=ROOT/'out/evaluation/validation.v84-joint.csv'
cmd=['build/core_template_estimate','--model','out/architecture-benchmark/core-template-xz6.bin','--vertical-transients','out/architecture-benchmark/vertical-transients-xz.bin','--horizontal-transients','out/architecture-benchmark/horizontal-transients.bin','--far-vertical-delta','out/architecture-benchmark/vertical-far-delta-xz.bin','--residual-model','out/v84/correction-128.bin','--trees','128','--joint-layout','--no-cache','-in','out/evaluation/validation.request.csv','-out',str(validation)]
r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True)
(ROOT/'out/v84/joint-validation.log').write_text(r.stderr)
same=validation.read_bytes()==(ROOT/'out/evaluation/validation.v84-128.csv').read_bytes();assert same
(ROOT/'reports/V84-joint-parity.json').write_text(json.dumps({'rows':150053,'byte_exact':same},indent=2)+'\n')

items=[]
for joint in (True,):
    trees=128
    log=ROOT/f'out/v84/speed10m-joint{int(joint)}.log';output=ROOT/'out/evaluation/speed10m-v84.output.csv'
    cmd=['/usr/bin/time','-l','build/core_template_estimate','--model','out/architecture-benchmark/core-template-xz6.bin','--vertical-transients','out/architecture-benchmark/vertical-transients-xz.bin','--horizontal-transients','out/architecture-benchmark/horizontal-transients.bin','--far-vertical-delta','out/architecture-benchmark/vertical-far-delta-xz.bin','--residual-model',f'out/v84/correction-{trees}.bin','--trees',str(trees),'-in','out/evaluation/speed10m-v45.request.csv','-out',str(output),'--no-cache']
    if joint:cmd.append("--joint-layout")
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True);log.write_text(r.stderr)
    cpu=float(re.search('cpu_seconds=([0-9.]+)',r.stderr)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',r.stderr)[1]);rows=int(re.search(r'rows=(\d+)',r.stderr)[1])
    assert rows==10000000
    files=[ROOT/'build/core_template_estimate',ROOT/'out/architecture-benchmark/core-template-xz6.bin',ROOT/'out/architecture-benchmark/vertical-transients-xz.bin',ROOT/'out/architecture-benchmark/horizontal-transients.bin',ROOT/f'out/v84/correction-{trees}.bin',ROOT/'out/architecture-benchmark/vertical-far-delta-xz.bin']
    items.append({'joint_layout':joint,'trees':trees,'rows':rows,'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':cpu-init,'requests_per_cpu_second':rows/(cpu-init),'runtime_file_bytes':sum(f.stat().st_size for f in files),'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',r.stderr)[1])});print(items[-1],flush=True)
    (ROOT/'reports/V84-piecewise-throughput.json').write_text(json.dumps({'state':'running','candidates':items},indent=2)+'\n')
report={'state':'complete','candidates':items,'scope':'10m repeated development requests, every row computed with prediction cache disabled, single runs. Actual CPU includes CSV input/output; no full billion proof, arbitrary hidden mix guarantee or official acceptance.'}
(ROOT/'reports/V84-piecewise-throughput.json').write_text(json.dumps(report,indent=2)+'\n')
