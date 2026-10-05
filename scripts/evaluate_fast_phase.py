"""Score a fixed validation candidate and record runtime; no holdout access."""
import argparse,csv,json,re,platform
import numpy as np
from architecture import ROOT

def main():
    a=argparse.ArgumentParser();a.add_argument('--name',required=True);a.add_argument('--prediction',required=True);a.add_argument('--log',required=True);a.add_argument('--reference');p=a.parse_args()
    with (ROOT/'out/evaluation/validation.golden.csv').open() as f:g=list(csv.DictReader(f))
    with (ROOT/p.prediction).open() as f:r=list(csv.DictReader(f))
    assert len(g)==len(r)==150053 and all((a['From'],a['To'])==(b['From'],b['To']) for a,b in zip(g,r))
    y=np.array([int(a['delay']) for a in g]);z=np.array([int(a['delay']) for a in r]);rel=np.abs(z-y)/np.maximum(y,1);log=(ROOT/p.log).read_text();cpu=re.search(r'cpu_seconds=([\d.]+)',log);rss=re.search(r'(\d+)\s+maximum resident set size',log);init=re.search(r'initialization_seconds=([\d.]+)',log)
    report={'fit_split':'development','selection_split':'validation','holdout_used':False,'rows':len(y),'validation_score':float(np.mean(100*(1-np.tanh(4*rel[y>0])))),'exact_fraction':float(np.mean(z==y)),'mean_relative_error':float(np.mean(rel[y>0])),'p99_relative_error':float(np.quantile(rel[y>0],.99)),'runtime':{'cpu_seconds':float(cpu[1]),'rss_bytes':int(rss[1]) if rss else None,'initialization_seconds':float(init[1]) if init else None},'machine':platform.platform(),'scope':'Approximate research candidate; no per-query precision certificate or official platform acceptance.'}
    if p.reference:
        reference=np.load(ROOT/p.reference);assert len(reference)==len(z);report['python_cpp_mismatch_rows']=int(np.sum(z!=reference));assert np.array_equal(z,reference)
    (ROOT/f'reports/{p.name}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
