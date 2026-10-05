"""Export compact float32 model weights for dependency-free C++ inference."""
import argparse,hashlib,json,struct
import numpy as np
import torch
from architecture import ROOT

def export(report_name,stem,kind,target):
    best=json.loads((ROOT/'reports'/report_name).read_text())['best'];checkpoint=torch.load(ROOT/best['model'],map_location='cpu',weights_only=True)
    state=checkpoint['state'];normal=np.load(ROOT/'out'/stem/'normalization.npz');routes=state['s.weight'].shape[1];numeric=len(normal['mean'])
    with target.open('wb') as f:
        f.write(b'ROUTENN1');f.write(struct.pack('<4Ifd',1,kind,numeric,routes,best['tau'],best['v19_weight']))
        f.write(normal['mean'].astype('<f4').tobytes());f.write(normal['std'].astype('<f4').tobytes());f.write(struct.pack('<I',len(state)))
        for name,value in sorted(state.items()):
            encoded=name.encode();v=value.numpy().astype('<f4').ravel();f.write(struct.pack('<I',len(encoded)));f.write(encoded);f.write(struct.pack('<I',len(v)));f.write(v.tobytes())
    return {'source':best,'file':str(target.relative_to(ROOT)),'kind':kind,'numeric_features':numeric,'routes':routes,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--phase-report',default='V27-minplus-neural.json');p.add_argument('--phase-stem',default='v27');args=p.parse_args()
    folder=ROOT/'models';folder.mkdir(exist_ok=True)
    reports=[export(args.phase_report,args.phase_stem,1,folder/'phase-route.bin'),export('V26-interval-minplus.json','v26',2,folder/'interval-route.bin')]
    (ROOT/'reports/Neural-route-export.json').write_text(json.dumps({'models':reports,'combined_bytes':sum(r['bytes'] for r in reports),'holdout_used':False},indent=2)+'\n');print(json.dumps(reports,indent=2),flush=True)

if __name__=='__main__':main()
