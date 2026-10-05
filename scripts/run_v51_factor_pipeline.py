"""Measure compact phase factors after the compiled-table experiment finishes."""
import argparse,csv,hashlib,json,os,re,subprocess,time
import numpy as np
from architecture import ROOT
from run_v51_pipeline import run

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wait-pid',type=int,required=True);args=parser.parse_args();path=ROOT/'reports/V51-cpp-architecture-comparison.json'
    while True:
        if path.exists():
            report=json.loads(path.read_text())
            if report.get('state')=='complete':break
        try:os.kill(args.wait_pid,0)
        except ProcessLookupError:raise RuntimeError('Table pipeline ended without a completed report; inspect it first')
        time.sleep(30)
    python=str(ROOT/'out/research-env/bin/python');folder=ROOT/'out/v51';result={'scope':'Factor versus precompiled-table CPU inference; same learned model; development-only training, no holdout','candidates':[]}
    for candidate in report['candidates']:
        h,r=candidate['hidden'],candidate['routes'];name=f'h{h}-r{r}';metadata=json.loads((folder/f'{name}.json').read_text());model=folder/f'{name}-factor.bin'
        run([python,'scripts/export_tiny_routes.py',metadata['source'],str(model),'--phase-format','factor'],folder/f'{name}-factor-export.log')
        pred=ROOT/f'out/evaluation/validation.v51-{name}-factor.csv';log=folder/f'{name}-factor-validation.log'
        run(['/usr/bin/time','-l',str(ROOT/'build/tiny_route_estimate'),'-in',str(ROOT/'out/evaluation/validation.request.csv'),'-out',str(pred),'--phase-bounds',str(ROOT/'models/phase-bounds-safe.bin'),'--model',str(model),'--no-cache'],log)
        run([python,'scripts/evaluate_fast_phase.py','--name',f'V51-{name}-factor-cpp','--prediction',str(pred.relative_to(ROOT)),'--log',str(log.relative_to(ROOT))],folder/f'{name}-factor-evaluation.log')
        evaluation=json.loads((ROOT/f'reports/V51-{name}-factor-cpp.json').read_text());raw=np.load(metadata['source'].replace('.pt','.npy'))
        with pred.open() as f:cpp=np.array([int(row['delay']) for row in csv.DictReader(f)])
        difference=np.abs(cpp-raw);evaluation['unquantized_python_mismatch_rows']=int(np.sum(difference>0));evaluation['unquantized_python_max_abs_difference_ps']=float(difference.max());assert difference.max()<=1
        speedlog=folder/f'{name}-factor-speed10m.log'
        run(['/usr/bin/time','-l',str(ROOT/'build/tiny_route_estimate'),'-in',str(ROOT/'out/evaluation/speed10m-v45.request.csv'),'-out',str(ROOT/'out/evaluation/speed10m-v51-factor.result.csv'),'--phase-bounds',str(ROOT/'models/phase-bounds-safe.bin'),'--model',str(model),'--no-cache'],speedlog)
        text=speedlog.read_text();cpu=float(re.search(r'cpu_seconds=([\d.]+)',text)[1]);item={'hidden':h,'routes':r,'cpp_evaluation':evaluation,'speed10m_cpu_seconds':cpu,'table_speed10m_cpu_seconds':candidate['speed10m_cpu_seconds'],'model_bytes':model.stat().st_size,'table_model_bytes':candidate['model_bytes'],'runtime_file_bytes':model.stat().st_size+(ROOT/'models/phase-bounds-safe.bin').stat().st_size+(ROOT/'build/tiny_route_estimate').stat().st_size,'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'model':str(model.relative_to(ROOT))};result['candidates'].append(item);(ROOT/'reports/V51-factor-architecture-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(item),flush=True)
    result['state']='complete';(ROOT/'reports/V51-factor-architecture-comparison.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
