"""Packed exact-double asymmetric trees, forward child indices per tree."""
import argparse,struct
import lightgbm as lgb
p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('--trees',type=int,required=True);a=p.parse_args()
m=lgb.Booster(model_file=a.source);trees=m.dump_model()['tree_info'][:a.trees];assert len(trees)==a.trees
with open(a.output,'wb') as f:
 f.write(b'ASYBND01');f.write(struct.pack('<I',len(trees)))
 for tree in trees:
  nodes=[]
  def emit(t):
   idx=len(nodes);nodes.append(None)
   if 'leaf_value' in t:nodes[idx]=(65535,float(t['leaf_value']));return idx
   assert t['decision_type']=='<=' and t['missing_type']=='None'
   left=emit(t['left_child']);right=emit(t['right_child']);nodes[idx]=(t['split_feature'],left,right,float(t['threshold']));return idx
  emit(tree['tree_structure']);assert len(nodes)<4096
  f.write(struct.pack('<H',len(nodes)))
  for node in nodes:
   if node[0]==65535:f.write(struct.pack('<Hd',*node))
   else:f.write(struct.pack('<HHHd',*node))
