"""Recreate the137-feature native baseline from frozen V242, no holdout input."""
import argparse,csv,hashlib,json,subprocess
from pathlib import Path
from architecture import ROOT
from native_research_labels import load_labels

p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--output',default='out/v243');a=p.parse_args()
runtime=Path(a.runtime);runtime=runtime if runtime.is_absolute() else ROOT/runtime
folder=ROOT/a.output;folder.mkdir(parents=True,exist_ok=True)
paths=[folder/f'all.{suffix}' for suffix in ('request.csv','csv','features.f32','base.i32')];assert not any(p.exists() for p in paths),'Do not overwrite an existing native feature dataset'
rows=[]
with paths[0].open('w') as output:
 writer=csv.DictWriter(output,fieldnames=['From','To'],lineterminator='\n');writer.writeheader()
 for split in ('development','validation'):
  count=0
  with (ROOT/f'out/evaluation/{split}.request.csv').open() as source:
   for row in csv.DictReader(source):writer.writerow({'From':row['From'],'To':row['To']});count+=1
  rows.append(count)
with (folder/'export.stderr').open('w') as log:
 subprocess.run([str(runtime/'estimate'),'-in',str(paths[0]),'-out',str(paths[1]),'--feature-out',str(paths[2]),'--base-out',str(paths[3])],stderr=log,cwd=ROOT,check=True)
assert paths[2].stat().st_size==sum(rows)*137*4 and paths[3].stat().st_size==sum(rows)*4
labels=load_labels();assert rows==[len(labels['y']),len(labels['yv'])]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
report={'state':'complete','development_rows':rows[0],'validation_rows':rows[1],'features':137,'holdout_used':False,'labels_supplied_to_native_estimator':False,'runtime_sha256':digest(runtime/'estimate'),'files':{p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in paths}}
(folder/'export-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
