"""Select reusable endpoint ports from development requests, without reading answers."""
import csv
import json
from architecture import Architecture,ROOT

def main():
    arch=Architecture();sources=set();targets=set()
    with (ROOT/'out/evaluation/development.request.csv').open() as f:
        for row in csv.DictReader(f):
            sources.add(arch.port_ids[row['From'].split('/')[1]])
            targets.add(arch.port_ids[row['To'].split('/')[1]])
    sources=sorted(sources);targets=sorted(targets)
    folder=ROOT/'out/local-oracle';folder.mkdir(parents=True,exist_ok=True)
    (folder/'ports.txt').write_text(f'{len(sources)} {len(targets)}\n'+' '.join(map(str,sources))+'\n'+' '.join(map(str,targets))+'\n')
    report={'source_ids':sources,'target_ids':targets,
            'selection':'development request endpoint names only; no delay labels',
            'local_x':12,'local_y':12,'patch_radius':28,
            'entries':len(sources)*len(targets)*25*25,
            'payload_bytes':len(sources)*len(targets)*25*25*4,'fit_used_golden':False}
    (folder/'ports.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('_ids')},indent=2))

if __name__=='__main__':main()
