"""Evaluate the fixed development strata with the exact reference implementation."""
import csv
import json
from architecture import ROOT
from verify_baseline import run

if __name__ == '__main__':
    with (ROOT/'out/stress/golden.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    result=run(f'development{len(rows)}_stratified',rows,'bidirectional')
    (ROOT/'out/stress/result_report.json').write_text(json.dumps(result,indent=2)+'\n')
