"""Validate request ordering, architecture-derived intervals, and competition score."""
import argparse,csv,json,re
import numpy as np
from architecture import ROOT

def read(path):
    with path.open() as f:return list(csv.DictReader(f))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',choices=['v39','v40'],required=True);args=parser.parse_args();v=args.version
    folder=ROOT/'out/evaluation';gold=read(folder/'validation.golden.csv');prediction=read(folder/f'validation.{v}-full.csv');cert=read(folder/f'validation.{v}-full.bounds.csv')
    assert len(prediction)==len(cert)==len(gold)==150053
    assert all((g['From'],g['To'])==(p['From'],p['To']) for g,p in zip(gold,prediction))
    assert [int(c['row']) for c in cert]==list(range(1,len(cert)+1))
    y=np.array([int(r['delay']) for r in gold],dtype=np.int64);p=np.array([int(r['delay']) for r in prediction],dtype=np.int64);lo=np.array([int(r['lower']) for r in cert],dtype=np.int64);hi=np.array([int(r['upper']) for r in cert],dtype=np.int64)
    interval_errors=int(np.sum((lo>y)|(hi<y)));prediction_errors=int(np.sum((p<lo)|(p>hi)));rel=np.abs(p-y)/np.maximum(y,1)
    assert interval_errors==prediction_errors==0
    eps=.00024;worst=np.maximum(np.abs(p-lo),np.abs(p-hi));allowed=np.floor(eps*lo).astype(np.int64)
    assert np.all(worst<=allowed),'Insufficient error certificates'
    log=(ROOT/f'out/{v}-full.log').read_text();cpu=re.search(r'cpu_seconds=([\d.]+)',log);rss=re.search(r'(\d+)\s+maximum resident set size',log)
    result={'fit_used_labels':False if v=='v40' else 'V27/V26 development-only models provide proposals; phase bound asset uses architecture only','holdout_used':False,'rows':len(y),'validation_score':float(np.mean(100*(1-np.tanh(4*rel[y>0])))),'mean_relative_error':float(np.mean(rel[y>0])),'max_relative_error':float(np.max(rel[y>0])),'p99_relative_error':float(np.quantile(rel[y>0],.99)),'exact_match_fraction':float(np.mean(p==y)),'exact_certificate_fraction':float(np.mean(lo==hi)),'invalid_intervals':interval_errors,'prediction_outside_interval':prediction_errors,'all_error_certificates_verified':True,'relative_error_limit':eps,'certified_minimum_score':float(100*(1-np.tanh(4*eps))),'runtime':{'cpu_seconds':float(cpu[1]),'max_rss_bytes':int(rss[1]),'mean_settled':float(np.mean([int(c['settled']) for c in cert]))},'scope':'Full fixed validation, not official hidden evaluation; search-based precision mode, not neural-only score; no billion-request acceptance.'}
    (ROOT/f'reports/{v.upper()}-full-certified-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
