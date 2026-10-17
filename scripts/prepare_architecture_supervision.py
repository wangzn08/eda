"""Prepare teacher seeds from development inputs; decode generated numeric labels."""
import argparse,csv,json
from architecture import ROOT,Architecture
p=argparse.ArgumentParser();p.add_argument('mode',choices=['seeds','decode']);p.add_argument('--count',type=int,default=32);args=p.parse_args()
a=Architecture();folder=ROOT/'out/v163';folder.mkdir(exist_ok=True)
if args.mode=='seeds':
 seeds=[];seen=set();seen_ports=set()
 with (ROOT/'out/evaluation/development.request.csv').open() as f:
  for row in csv.DictReader(f):
   node=a.pin(row['From'])[2];port=node%len(a.ports)
   if port not in seen_ports and node not in seen:
    seeds.append(node);seen.add(node);seen_ports.add(port)
   if len(seeds)>=args.count:break
 (folder/'seeds.txt').write_text(''.join(f'{s}\n' for s in seeds))
 (folder/'seed-manifest.json').write_text(json.dumps({'source':'development inputs only','seed_count':len(seeds),'seed_nodes':seeds,'target_source':'architecture-only deterministic random sampling','validation_labels_used':False,'holdout_used':False},indent=2)+'\n')
else:
 def pin(n):
  s,p=divmod(int(n),len(a.ports));return a.instances[s]['name']+'/'+a.ports[p]['Name']
 with (folder/'teacher.numeric.csv').open() as f,(folder/'teacher.request.csv').open('w') as q,(folder/'teacher.golden.csv').open('w') as g:
  qw=csv.writer(q);gw=csv.writer(g);qw.writerow(['From','To']);gw.writerow(['From','To','delay'])
  for r in csv.DictReader(f):
   s,t=pin(r['source']),pin(r['target']);qw.writerow([s,t]);gw.writerow([s,t,r['delay']])
