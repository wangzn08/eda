"""Export the selected LightGBM residual as standalone C++ numeric trees."""
import json
import lightgbm as lgb

from architecture import Architecture,ROOT
from v4_features import FeatureBuilder,NAMES


def main():
    report=json.loads((ROOT/'reports/V4-tree-research.json').read_text())
    selected=report['best']
    model=lgb.Booster(model_file=str(ROOT/'out/v4'/f"{selected['model']}.txt"))
    dumped=model.dump_model()
    nodes=[];roots=[]
    def emit(branch):
        index=len(nodes);nodes.append(None)
        if 'split_feature' not in branch:
            nodes[index]=(65535,0,0,0.,float(branch['leaf_value']))
            return index
        if branch['decision_type']!='<=' or branch['missing_type']!='None':
            raise ValueError('Unsupported LightGBM node semantics')
        left=emit(branch['left_child']);right=emit(branch['right_child'])
        nodes[index]=(int(branch['split_feature']),left,right,float(branch['threshold']),0.)
        return index
    for entry in dumped['tree_info'][:selected['trees']]:
        roots.append(emit(entry['tree_structure']))
    arch=Architecture()
    builder=FeatureBuilder()
    family=[builder.family(p['Name']) for p in arch.ports]
    def prefix(size,vertical):
        return [sum(g['delay'] for g in arch.lines
                    if (g['direction']=='vertical')==vertical and g['site']<i)
                for i in range(size+1)]
    xp=prefix(arch.width,True);yp=prefix(arch.height,False)
    path=ROOT/'src/v4_tree_model.hpp'
    text='\n'.join([
        '// LightGBM 4.6.0 numeric tree export; fitted on development labels only.',
        '#pragma once','#include <array>','#include <cstdint>','namespace v4_tree_model {',
        'struct Node {uint16_t feature; uint32_t left,right; double threshold,value;};',
        f'constexpr std::array<uint32_t,{len(roots)}> roots={{{",".join(map(str,roots))}}};',
        f'constexpr std::array<Node,{len(nodes)}> nodes={{{{',
        *('  {'+','.join((str(f),str(l),str(r),format(t,'.17g'),format(v,'.17g')))+'},'
          for f,l,r,t,v in nodes),
        '}};',
        f'constexpr std::array<uint8_t,{len(family)}> family={{{",".join(map(str,family))}}};',
        f'constexpr std::array<uint16_t,{len(xp)}> x_gap_prefix={{{",".join(map(str,xp))}}};',
        f'constexpr std::array<uint16_t,{len(yp)}> y_gap_prefix={{{",".join(map(str,yp))}}};',
        '} // namespace v4_tree_model',''])
    path.write_text(text)
    export={'source':str(path),'bytes':path.stat().st_size,'trees':len(roots),'nodes':len(nodes),
            'features':list(NAMES),'blend':selected['blend'],'python_validation_score':selected['score'],
            'holdout_used':False}
    (ROOT/'reports/V4-tree-export.json').write_text(json.dumps(export,indent=2)+'\n')
    print(json.dumps(export,indent=2))


if __name__=='__main__':main()
