"""Export the validation-selected V9 residual model as standalone numeric trees."""
import json
import lightgbm as lgb
from architecture import ROOT

def main():
    report=json.loads((ROOT/'reports/V9-topology-research.json').read_text())
    selected=report['best']
    model=lgb.Booster(model_file=str(ROOT/selected['model']))
    nodes=[];roots=[]
    def emit(branch):
        index=len(nodes);nodes.append(None)
        if 'split_feature' not in branch:
            nodes[index]=(65535,0,0,0.,float(branch['leaf_value']));return index
        if branch['decision_type']!='<=' or branch['missing_type']!='None':
            raise ValueError('Unsupported tree semantics')
        left=emit(branch['left_child']);right=emit(branch['right_child'])
        nodes[index]=(int(branch['split_feature']),left,right,float(branch['threshold']),0.)
        return index
    for tree in model.dump_model()['tree_info'][:selected['trees']]:
        roots.append(emit(tree['tree_structure']))
    path=ROOT/'src/v9_tree_model.hpp'
    lines=['// Development-trained V9 residual; validation-selected tree count.',
           '#pragma once','#include <array>','#include <cstdint>','namespace v9_tree_model {',
           'struct Node {uint16_t feature; uint32_t left,right; double threshold,value;};',
           f'constexpr double blend={selected.get("blend",1.0)};',
           f'constexpr std::array<uint32_t,{len(roots)}> roots={{{",".join(map(str,roots))}}};',
           f'constexpr std::array<Node,{len(nodes)}> nodes={{{{',
           *('  {'+','.join((str(f),str(l),str(r),format(t,'.17g'),format(v,'.17g')))+'},' for f,l,r,t,v in nodes),
           '}};','} // namespace v9_tree_model','']
    path.write_text('\n'.join(lines))
    result={'source':str(path),'source_bytes':path.stat().st_size,'nodes':len(nodes),
            'trees':len(roots),'python_validation_score':selected['oracle_score'],
            'holdout_used':False}
    (ROOT/'reports/V9-tree-export.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
