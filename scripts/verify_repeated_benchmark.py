"""Run the official CLI repeatedly on a fixed large request file.

Results are saved after each run, so an interrupted benchmark is inspectable.
"""
import argparse
import hashlib
import json
import platform
import re
import subprocess
import time
from pathlib import Path

from architecture import ROOT


def digest(path):
    sha=hashlib.sha256()
    with path.open('rb') as f:
        while block:=f.read(8*1024*1024): sha.update(block)
    return sha.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--rows',type=int,required=True)
    parser.add_argument('--runs',type=int,default=5)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.runs<1 or args.rows<1:raise ValueError('runs and rows must be positive')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    exe=ROOT/'build/estimate'
    command=[str(exe),'-in',str(args.input),'-out',str(args.output)]
    result={'input':str(args.input),'input_bytes':args.input.stat().st_size,
            'output':str(args.output),'expected_rows':args.rows,'command':command,
            'machine':platform.platform(),'architecture':platform.machine(),
            'binary_sha256':digest(exe),'runs':[]}
    for i in range(args.runs):
        print(json.dumps({'phase':'run','index':i+1,'total':args.runs}),flush=True)
        start=time.monotonic()
        timed=['/usr/bin/time','-l',*command] if platform.system()=='Darwin' else command
        process=subprocess.run(timed,capture_output=True,text=True,timeout=3600)
        elapsed=time.monotonic()-start
        if process.returncode:raise RuntimeError(f'Run {i+1} failed: {process.stderr}')
        match=re.search(r'rows=(\d+) cpu_seconds=([0-9.]+)',process.stderr)
        if not match or int(match.group(1))!=args.rows:
            raise RuntimeError(f'Run {i+1} wrote wrong row count: {process.stderr}')
        peak=re.search(r'(\d+)\s+maximum resident set size',process.stderr)
        entry={'index':i+1,'rows':int(match.group(1)),
               'process_cpu_seconds':float(match.group(2)),
               'wall_seconds':elapsed,'peak_rss_bytes':int(peak.group(1)) if peak else None,
               'output_bytes':args.output.stat().st_size,
               'output_sha256':digest(args.output)}
        result['runs'].append(entry)
        args.report.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'phase':'complete',**entry}),flush=True)
        if entry['output_sha256']!=result['runs'][0]['output_sha256']:
            raise RuntimeError(f'Run {i+1} output differs from run 1')
    result['all_outputs_identical']=True
    args.report.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
