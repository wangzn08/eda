"""After the V50 CPU benchmark, train and measure alternate small min-plus models."""
import csv,hashlib,json,re,subprocess,time
from pathlib import Path
import numpy as np
from architecture import ROOT

def run(command,log):
    with log.open('wb') as f:subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)

def main():
    python=str(ROOT/'out/research-env/bin/python');folder=ROOT/'out/v51';folder.mkdir(exist_ok=True)
    run([python,'-u','scripts/experiment_v51_tiny_routes.py','--wait-benchmark'],folder/'train.log')
    training=json.loads((ROOT/'reports/V51-tiny-routes.json').read_text());report={'fit_split':'development','holdout_used':False,'architecture':'Small PDB anchored latent route model; precompiled endpoint phases, int16 tables, hard minimum, vectorized output-channel loops','scope':'Approximate research models, not per-query certified; 10m no-cache throughput is not billion or official acceptance','candidates':[]}
    for hidden,routes in [(64,128),(128,128),(64,64)]:
        best=max((r for r in training['candidates'] if r['hidden']==hidden and r['routes']==routes),key=lambda r:r['validation_score']);name=f'h{hidden}-r{routes}';model=folder/f'{name}.bin'
        run([python,'scripts/export_tiny_routes.py',str(ROOT/best['weights']),str(model)],folder/f'{name}-export.log')
        pred=ROOT/f'out/evaluation/validation.v51-{name}.csv';log=folder/f'{name}-validation.log'
        run(['/usr/bin/time','-l',str(ROOT/'build/tiny_route_estimate'),'-in',str(ROOT/'out/evaluation/validation.request.csv'),'-out',str(pred),'--phase-bounds',str(ROOT/'models/phase-bounds-safe.bin'),'--model',str(model),'--no-cache'],log)
        run([python,'scripts/evaluate_fast_phase.py','--name',f'V51-{name}-cpp','--prediction',str(pred.relative_to(ROOT)),'--log',str(log.relative_to(ROOT))],folder/f'{name}-evaluation.log')
        evaluation=json.loads((ROOT/f'reports/V51-{name}-cpp.json').read_text());raw=np.load(ROOT/best['weights'].replace('.pt','.npy'))
        with pred.open() as f:cpp=np.array([int(r['delay']) for r in csv.DictReader(f)])
        difference=np.abs(cpp-raw);evaluation['unquantized_python_mismatch_rows']=int(np.sum(difference>0));evaluation['unquantized_python_max_abs_difference_ps']=float(np.max(difference));assert difference.max()<=1,'Export/inference deviates by more than 1 ps; inspect before benchmarking'
        speedlog=folder/f'{name}-speed10m.log'
        run(['/usr/bin/time','-l',str(ROOT/'build/tiny_route_estimate'),'-in',str(ROOT/'out/evaluation/speed10m-v45.request.csv'),'-out',str(ROOT/'out/evaluation/speed10m-v51.result.csv'),'--phase-bounds',str(ROOT/'models/phase-bounds-safe.bin'),'--model',str(model),'--no-cache'],speedlog)
        text=speedlog.read_text();cpu=float(re.search(r'cpu_seconds=([\d.]+)',text)[1]);item={'hidden':hidden,'routes':routes,'epoch':best['epoch'],'cpp_evaluation':evaluation,'speed10m_cpu_seconds':cpu,'model_bytes':model.stat().st_size,'runtime_file_bytes':model.stat().st_size+(ROOT/'models/phase-bounds-safe.bin').stat().st_size+(ROOT/'build/tiny_route_estimate').stat().st_size,'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'within_10m_36s_budget':cpu<=36,'model':str(model.relative_to(ROOT))}
        report['candidates'].append(item);(ROOT/'reports/V51-cpp-architecture-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(item),flush=True)
    report['state']='complete';(ROOT/'reports/V51-cpp-architecture-comparison.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
