"""P4 gate: compare projected graph with the archived exact reference."""
import csv
import json
from pathlib import Path
from architecture import DEFAULT_ARCH, ROOT
from verify_baseline import run


def main():
    cases=[('official8_compressed',DEFAULT_ARCH.parent/'data/delay_estimate_check.csv','official8_bidirectional'),
           ('development44_compressed',ROOT/'out/stress/golden.csv','development44_stratified'),
           ('development8_zero_compressed',ROOT/'out/baseline/development8_zero_repeats.request.csv',None)]
    results=[]
    for name,path,reference in cases:
        with path.open(newline='') as f: rows=list(csv.DictReader(f))
        if name=='development8_zero_compressed':
            with (ROOT/'out/baseline/development8_zero_repeats.result.csv').open(newline='') as f:
                answer=list(csv.DictReader(f))
            rows=[{**r,'delay':answer[i]['delay']} for i,r in enumerate(rows)]
        result=run(name,rows,'compressed')
        if reference:
            with (ROOT/f'out/baseline/{reference}.result.csv').open('rb') as f:
                import hashlib
                assert hashlib.sha256(f.read()).hexdigest()==result['output_sha256']
        results.append(result)
    (ROOT/'out/compression_verification.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':
    main()
