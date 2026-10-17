import json,csv,re
import numpy as np
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v7_teacher import score
_,y,_,_=load('validation');expected=np.load(ROOT/'out/v125/fit-features.npz')['bv'];rows=[]
for name in ('v151-prepared','v152-staged','v153-libdecoder','v154-sparse'):
 folder=ROOT/'out'/name;text=(folder/'pilot.stderr').read_text();assert 'rows=1150053' in text
 with (folder/'pilot.csv').open() as f:p=np.array([int(row['delay']) for _,row in zip(range(150053),csv.DictReader(f))])
 assert np.array_equal(p,expected);checkpoint=float(re.search('checkpoint_cpu_seconds=([0-9.]+)',text)[1]);cpu=float(re.search('cpu_seconds=([0-9.]+) initialization',text)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',text)[1]);rows.append({'name':name,'validation_score':score(y,p),'validation_parity':True,'init_seconds':init,'query_1m_cpu_seconds':cpu-checkpoint,'billion_pilot_seconds':init+1000*(cpu-checkpoint),'runtime_artifact_bytes':sum(p.stat().st_size for p in folder.iterdir() if p.suffix=='.bin' or p.name=='estimate')})
r={'state':'complete','scope':'Serial1m screening with full validation prefix; not paired10m or official Linux; pilot outputs outside packaging','holdout_used':False,'cases':rows};(ROOT/'reports/V151-V154-index-pilots.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
