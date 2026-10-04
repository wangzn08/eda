"""Measure frozen V14 CLI, scores, deterministic repeats and resources."""
import argparse,csv,hashlib,json,platform,re,subprocess,time
from pathlib import Path
from architecture import ROOT
from evaluate import metrics

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def run(exe,request,out,extra=()):
    command=[str(exe),'-in',str(request),'-out',str(out),*extra]
    timed=['/usr/bin/time','-l',*command] if platform.system()=='Darwin' else command
    start=time.monotonic();p=subprocess.run(timed,capture_output=True,text=True,cwd=exe.parent,timeout=3600)
    out.with_suffix('.log').write_text(p.stderr)
    if p.returncode:raise RuntimeError(p.stderr)
    m=re.search(r'rows=(\d+) cpu_seconds=([0-9.]+)',p.stderr)
    rss=re.search(r'(\d+)\s+maximum resident set size',p.stderr)
    cache=re.search(r'cache_hits=(\d+) cache_misses=(\d+)',p.stderr)
    return {'command':command,'rows':int(m[1]),'cpu_seconds':float(m[2]),'wall_seconds':time.monotonic()-start,
      'peak_rss_bytes':int(rss[1]) if rss else None,'output_bytes':out.stat().st_size,'sha256':digest(out),
      'cache_hits':int(cache[1]) if cache else None,'cache_misses':int(cache[2]) if cache else None}

def score(golden,result):
    with golden.open(newline='') as f,result.open(newline='') as g:return metrics(list(csv.DictReader(f)),list(csv.DictReader(g)))

def main():
    p=argparse.ArgumentParser();p.add_argument('--billion',action='store_true');p.add_argument('--billion-only',action='store_true');p.add_argument('--runs',type=int,default=5);args=p.parse_args()
    root=ROOT/'out/acceptance-v14';exe=root/'extracted/fpga-delay-estimator-v14/estimate'
    report_path=ROOT/'reports/V14-acceptance.json'
    report={'machine':platform.platform(),'binary_sha256':digest(exe),'model_frozen':json.loads((root/'bundle/manifest.json').read_text())['model_frozen_sha256'],
      'phase':'initial','checks':{},'billion_runs':[]}
    def save():report_path.write_text(json.dumps(report,indent=2)+'\n')
    def check(name,request,golden=None,extra=()):
        print('RUN '+name,flush=True);out=root/(name+'.csv');r=run(exe,request,out,extra)
        if golden:r['metrics']=score(golden,out)
        report['checks'][name]=r;save();print(json.dumps({'done':name,**r},ensure_ascii=False),flush=True);return r
    if args.billion_only:
        report=json.loads(report_path.read_text())
        assert report['binary_sha256']==digest(exe)
        h=report['checks']['holdout']
    else:
        v=check('validation',ROOT/'out/evaluation/validation.request.csv',ROOT/'out/evaluation/validation.golden.csv')
        raw=check('validation-no-cache',ROOT/'out/evaluation/validation.request.csv',extra=('--no-cache',))
        assert raw['sha256']==v['sha256'];report['cache_does_not_change_output']=True
        h=check('holdout',ROOT/'out/evaluation/holdout.request.csv',ROOT/'out/evaluation/holdout.golden.csv')
        check('public-million',root/'public.request.csv',ROOT/'data/EDA-PANGO-SRB-Arch-Delay/data/delay_estimate_ans.csv')
    if args.billion or args.billion_only:
        request=root/'stress1b.request.csv';output=root/'stress1b.result.csv'
        if not request.exists():raise ValueError('Prepare stress1b.request.csv first')
        report['phase']='billion';save()
        for i in range(args.runs):
            print(f'RUN billion {i+1}/{args.runs}',flush=True)
            r=run(exe,request,output);r['index']=i+1
            assert r['rows']==1000000000
            if report['billion_runs']:assert r['sha256']==report['billion_runs'][0]['sha256']
            report['billion_runs'].append(r);save();print(json.dumps(r),flush=True)
        avg=sum(r['cpu_seconds'] for r in report['billion_runs'])/len(report['billion_runs'])
        time_score=100*max(0,1-avg/1800)
        report.update(average_billion_cpu_seconds=avg,time_score=time_score,all_billion_outputs_identical=True,
          all_billion_runs_within_limits=all(r['cpu_seconds']<=3600 and r['peak_rss_bytes']<=2000000000 for r in report['billion_runs']),
          local_simulated_total=h['metrics']['positive_delay_score']*.8+time_score*.15+5)
    report['phase']='complete';save()

if __name__=='__main__':main()
