"""Expand certified cycle hop enumeration without changing path semantics."""
import csv,json,subprocess,time
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score

def prepare():
    folder=ROOT/'out/v18';folder.mkdir(exist_ok=True)
    source=(ROOT/'src/cycle_path_oracle.hpp').read_text()
    source=source.replace('hops-int(extra_hops)', 'hops-1').replace('count-int(extra_hops)', 'count-1')
    (folder/'cycle_path_oracle.hpp').write_text(source)
    (folder/'cycle_oracle_apply.cpp').write_text((ROOT/'src/cycle_oracle_apply.cpp').read_text())
    subprocess.run(['c++','-std=c++17','-O3','-I',str(ROOT/'src'),str(folder/'cycle_oracle_apply.cpp'),'-o',str(folder/'cycle_oracle_apply')],check=True)

def load(path):
    with path.open() as f:return list(csv.DictReader(f))

def main():
    prepare();root=ROOT/'out/evaluation';folder=ROOT/'out/v18'
    start=time.monotonic()
    subprocess.run([str(folder/'cycle_oracle_apply'),str(root/'validation.v13-bound.csv'),str(root/'validation.v18-bound.csv'),str(ROOT/'out/local-oracle/long-tail-12-dict.bin')],check=True)
    g=load(root/'validation.golden.csv');old=load(root/'validation.v13-bound.csv');new=load(root/'validation.v18-bound.csv');prior=load(ROOT/'out/acceptance-v14/validation.csv')
    assert len(g)==len(old)==len(new)==len(prior)
    for a,b,c,d in zip(g,old,new,prior):assert (a['From'],a['To'])==(b['From'],b['To'])==(c['From'],c['To'])==(d['From'],d['To'])
    y=np.array([int(r['delay']) for r in g]);u=np.array([int(r['delay']) for r in new]);uo=np.array([int(r['delay']) for r in old]);p=np.array([int(r['delay']) for r in prior]);pred=np.minimum(p,u)
    assert np.all(u>=y),'A feasible upper bound must never fall below shortest distance'
    assert np.all(u<=uo)
    np.save(folder/'validation-capped.npy',pred)
    report={'fit_used_labels':False,'holdout_used':False,'before_score':score(y,p),'after_score':score(y,pred),
        'bounds_lowered':int((u<uo).sum()),'predictions_changed':int((pred!=p).sum()),'bound_exact_matches_before':int((uo==y).sum()),
        'bound_exact_matches_after':int((u==y).sum()),'upper_bound_violations':0,'elapsed_seconds':time.monotonic()-start,
        'proof':'Additional candidates concatenate the same validated entry witnesses, official straight long-wire cycles, turn arcs and translated tail witnesses. Expanded hop enumeration does not relax any boundary/Block/Gap certificate.'}
    (ROOT/'reports/V18-hop-window.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
