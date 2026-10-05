"""Evaluate certified macro paths and model combinations at distinct search budgets."""
import csv,json,subprocess,time
import numpy as np
from architecture import ROOT
from experiment_v7_teacher import score

def main():
    root=ROOT/'out/evaluation';prior=np.load(ROOT/'out/v19/validation-1536.npy')
    with (root/'validation.golden.csv').open() as f:gold=list(csv.DictReader(f))
    y=np.array([int(r['delay']) for r in gold]);nn=json.loads((ROOT/'reports/V21-neural-architecture.json').read_text())['best']
    hybrid=np.load(ROOT/f"out/v21/validation-{int(nn['graph_embedding'])}-{nn['epoch']}-{nn['v19_weight']}.npy")
    results=[]
    for budget in (256,1024,4096):
        path=root/f'validation.v22-{budget}-bound.csv';start=time.monotonic()
        run=subprocess.run([str(ROOT/'build/macro_oracle_apply'),str(root/'validation.v18-bound.csv'),str(path),str(ROOT/'out/local-oracle/long-tail-12-dict.bin'),str(budget)],capture_output=True,text=True,check=True)
        (ROOT/f'out/v22-{budget}.log').write_text(run.stderr)
        with path.open() as f:rows=list(csv.DictReader(f))
        assert len(rows)==len(gold)
        assert all((a['From'],a['To'])==(b['From'],b['To']) for a,b in zip(rows,gold))
        u=np.array([int(r['delay']) for r in rows]);assert np.all(u>=y)
        item={'budget':budget,'wall_seconds':time.monotonic()-start,'upper_bound_violations':0,'bound_exact_matches':int((u==y).sum()),
            'v19_capped_score':score(y,np.minimum(prior,u)),'neural_hybrid_capped_score':score(y,np.minimum(hybrid,u)),'log':run.stderr.splitlines()[-1]}
        np.save(ROOT/f'out/architecture-benchmark/validation-macro-{budget}.npy',np.minimum(hybrid,u));results.append(item);print(json.dumps(item),flush=True)
        (ROOT/'reports/V22-macro-path-architecture.json').write_text(json.dumps({'fit_used_labels':False,'holdout_used':False,'baseline_v19':score(y,prior),
            'baseline_neural_hybrid':score(y,hybrid),'candidates':results,'best':max(results,key=lambda x:x['neural_hybrid_capped_score']),
            'scope':'Bounded A* on long-input transit vertices with certified local and official arc/net edges; a subset of full routing graph, not an exact solver for every query.'},indent=2)+'\n')

if __name__=='__main__':main()
