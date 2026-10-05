"""Compare C++ expanded-cycle predictions with independent validation capping."""
import csv,hashlib,json,subprocess,time
import numpy as np
from architecture import ROOT
from evaluate import metrics

def main():
    request=ROOT/'out/evaluation/validation.request.csv';output=ROOT/'out/evaluation/validation.v18-cpp.csv'
    command=[str(ROOT/'build/estimate'),'-in',str(request),'-out',str(output),'--algorithm','v14-tree',
      '--local-oracle',str(ROOT/'out/local-oracle/factorized-20-planes.bin'),'--cycle-oracle',str(ROOT/'out/local-oracle/long-tail-12-dict.bin'),'--cycle-extra-hops']
    start=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,check=True)
    (ROOT/'out/v18-cpp.log').write_text(r.stderr)
    with output.open() as f:p=list(csv.DictReader(f))
    with (ROOT/'out/evaluation/validation.golden.csv').open() as f:g=list(csv.DictReader(f))
    expected=np.load(ROOT/'out/v18/validation-capped.npy');assert np.array_equal(np.array([int(x['delay']) for x in p]),expected)
    report={'metrics':metrics(g,p),'cpp_equals_independent_capping':True,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
      'command':command,'holdout_used':False,'wall_seconds':time.monotonic()-start,'stderr':r.stderr}
    (ROOT/'reports/V18-cpp-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['metrics']),flush=True)

if __name__=='__main__':main()
