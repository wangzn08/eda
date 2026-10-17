"""Export numeric CatBoost oblivious trees without a runtime CatBoost dependency."""
import argparse,json,struct
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--trees',type=int,default=1024);p.add_argument('--obstacle-phase',action='store_true');p.add_argument('--boundary',action='store_true');a=p.parse_args();model=json.loads(a.source.read_text());trees=model['oblivious_trees'][:a.trees];assert len(trees)==a.trees and a.trees>0
    with a.output.open('wb') as f:
        f.write(b'FASTBND1' if a.boundary else b'FASTOBS1' if a.obstacle_phase else b'FASTRES1');f.write(struct.pack('<Idd',len(trees),model['scale_and_bias'][0],model['scale_and_bias'][1][0]))
        for t in trees:
            f.write(struct.pack('<I',len(t['splits'])))
            for s in t['splits']:
                assert s['split_type']=='FloatFeature';f.write(struct.pack('<If',s['float_feature_index'],s['border']))
            f.write(struct.pack('<'+'d'*len(t['leaf_values']),*t['leaf_values']))
    print(a.output,a.output.stat().st_size)

if __name__=='__main__':main()
