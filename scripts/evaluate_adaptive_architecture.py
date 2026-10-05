"""Report validation-only architecture comparisons with endpoint/order checks."""
import argparse,csv,json,re
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score

def read(path):
    with path.open() as f:return list(csv.DictReader(f))

def aligned(rows,gold):
    assert len(rows)==len(gold),(len(rows),len(gold))
    assert all((a['From'],a['To'])==(b['From'],b['To']) for a,b in zip(rows,gold))
    return np.array([int(a['delay']) for a in rows],dtype=np.float64)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prediction',default='validation.v35-adaptive.csv');parser.add_argument('--log',default='v35-adaptive.log');args=parser.parse_args()
    folder=ROOT/'out/evaluation';gold=read(folder/'validation.golden.csv');y=aligned(gold,gold);lookup={(r['From'],r['To']):int(r['delay']) for r in gold}
    references={}
    for name in ('validation.v33-short-exact.csv','validation.v34-short-astar.csv','validation.v34-uncertain-exact.csv'):
        rows=read(folder/name);errors=[int(r['delay'])-lookup[(r['From'],r['To'])] for r in rows];references[name]={'rows':len(rows),'golden_mismatches':sum(e!=0 for e in errors),'max_abs_error_ps':max(map(abs,errors),default=0)}
        assert references[name]['golden_mismatches']==0,(name,references[name])
    variants={}
    for name in ('validation.v19-cpp.csv','validation.v30-final-cpp.csv',args.prediction):
        p=aligned(read(folder/name),gold);relative=np.abs(p-y)/np.maximum(y,1);variants[name]={'rows':len(p),'validation_score':score(y,p),'exact_match_fraction':float(np.mean(p==y)),'mean_relative_error':float(np.mean(relative)),'p99_relative_error':float(np.quantile(relative,.99))}
    log=(ROOT/'out'/args.log).read_text();cpu=re.search(r'cpu_seconds=([\d.]+)',log);rss=re.search(r'(\d+)\s+maximum resident set size',log);counts=re.search(r'exact_short_queries=(\d+) exact_uncertain_queries=(\d+)',log)
    report={'fit_split':'development','selection_split':'validation','holdout_used':False,'variants':variants,'exact_reference_checks':references,'runtime':{'cpu_seconds':float(cpu[1]) if cpu else None,'max_rss_bytes':int(rss[1]) if rss else None,'short_exact_queries':int(counts[1]) if counts else None,'uncertain_exact_queries':int(counts[2]) if counts else None},'selection':{'short_manhattan_less_than':25,'model_relative_disagreement_greater_than':.01,'neural_phase_weight':.75,'neural_interval_weight':.25,'macro_expansion_budget':65536},'caveats':['Validation selected candidates; this is not an independent final score.','Adaptive result includes exact A* fallback; it is not neural-only accuracy.','No holdout or billion-request acceptance was run.','Unique-query throughput is not competition compliant.']}
    target=ROOT/'reports/V35-adaptive-validation.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
