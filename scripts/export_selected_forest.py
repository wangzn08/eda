"""Export numeric L1 trees and exact feature schema for standalone C++."""
import argparse,hashlib,json,re,struct
from pathlib import Path
import lightgbm as lgb
from architecture import ROOT,Architecture
p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('features');p.add_argument('output');p.add_argument('--schema',required=True);args=p.parse_args()
names=json.loads(Path(args.features).read_text());assert len(names)==137 and names[69]=='response_0' and names[77]=='source_phi_0' and names[125]=='source_direction_phi_0_0'
schema_hash=hashlib.sha256(json.dumps(names,separators=(',',':')).encode()).hexdigest();arch=Architecture();arch_hash=re.search(r'constexpr char HASH\[\]="([a-f0-9]{64})"',(ROOT/'src/architecture_data.hpp').read_text())[1];model=lgb.Booster(model_file=args.model);dump=model.dump_model();assert dump['max_feature_idx']+1==len(names) and not dump.get('average_output',False)
with Path(args.output).open('wb') as f:
    f.write(b'SFRST001'+arch_hash.encode()+schema_hash.encode());f.write(struct.pack('<2I',len(names),len(dump['tree_info'])))
    for tree in dump['tree_info']:
        nodes=[]
        def visit(v):
            i=len(nodes);nodes.append(None)
            if 'leaf_value' in v:nodes[i]=(65535,0,0,0,float(v['leaf_value']))
            else:
                assert v['decision_type']=='<=';left=visit(v['left_child']);right=visit(v['right_child']);nodes[i]=(v['split_feature'],left,right,0,float(v['threshold']))
            return i
        assert visit(tree['tree_structure'])==0;assert len(nodes)<65536;f.write(struct.pack('<I',len(nodes)))
        for n in nodes:f.write(struct.pack('<HHHHd',*n))
categories={};types=[];lanes=[]
for port in arch.ports:
    m=re.fullmatch(r'(.*)\[(\d+)\]',port['Name']);name=m[1] if m else port['Name'];types.append(categories.setdefault(name,len(categories)));lanes.append(int(m[2]) if m else -1)
text='#pragma once\n// Generated from the training feature order and architecture names.\nnamespace selectedschema {\nconstexpr unsigned COUNT=137;\nconstexpr char HASH[]="'+schema_hash+'";\n'
for name,a in [('PORT_TYPE',types),('PORT_LANE',lanes)]:text+='constexpr int '+name+'[]={'+','.join(map(str,a))+'};\n'
text+='}\n';Path(args.schema).write_text(text);print(json.dumps({'bytes':Path(args.output).stat().st_size,'trees':len(dump['tree_info']),'features':len(names),'schema_sha256':schema_hash}))
