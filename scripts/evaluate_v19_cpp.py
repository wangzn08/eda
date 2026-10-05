"""Compare C++ route-bound model with independent Python predictions."""
import csv,hashlib,json,subprocess,time
import numpy as np
from architecture import ROOT
from evaluate import metrics

def main():
    request=ROOT/'out/evaluation/validation.request.csv';output=ROOT/'out/evaluation/validation.v19-cpp.csv'
    command=[str(ROOT/'build/estimate'),'-in',str(request),'-out',str(output),'--algorithm','v19-tree',
      '--local-oracle',str(ROOT/'out/local-oracle/factorized-20-planes.bin'),'--cycle-oracle',str(ROOT/'out/local-oracle/long-tail-12-dict.bin')]
    start=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,check=True)
    (ROOT/'out/v19-cpp.log').write_text(r.stderr)
    with output.open() as f:p=list(csv.DictReader(f))
    with (ROOT/'out/evaluation/validation.golden.csv').open() as f:g=list(csv.DictReader(f))
    expected=np.load(ROOT/'out/v19/validation-1536.npy');assert np.array_equal(np.array([int(x['delay']) for x in p]),expected)
    report={'metrics':metrics(g,p),'cpp_equals_python':True,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
      'command':command,'holdout_used':False,'wall_seconds':time.monotonic()-start,'stderr':r.stderr}
    (ROOT/'reports/V19-cpp-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['metrics']),flush=True)

if __name__=='__main__':main()
