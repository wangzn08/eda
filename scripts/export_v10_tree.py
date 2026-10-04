"""Export the validation-selected V10 residual model as standalone numeric trees."""
import json
import struct
import numpy as np
import lightgbm as lgb
from architecture import ROOT

def main():
    report=json.loads((ROOT/'reports/V10-wire-research.json').read_text())
    selected=report['best']
    model=lgb.Booster(model_file=str(ROOT/selected['model']))
    payload=bytearray();roots=[];node_count=0
    def emit(branch):
        nonlocal node_count
        node_count+=1;offset=len(payload)
        if 'split_feature' not in branch:
            payload.extend(struct.pack('<Bd',255,float(branch['leaf_value'])));return offset
        if branch['decision_type']!='<=' or branch['missing_type']!='None':raise ValueError('Unsupported tree semantics')
        threshold=float(branch['threshold']);t=np.float32(threshold)
        if float(t)>threshold:t=np.nextafter(t,np.float32(-np.inf))
        payload.extend(struct.pack('<BHf',int(branch['split_feature']),0,float(t)))
        emit(branch['left_child']);right=emit(branch['right_child'])
        if right-offset>65535:raise ValueError('Relative tree branch too large')
        struct.pack_into('<H',payload,offset+1,right-offset)
        return offset
    for tree in model.dump_model()['tree_info'][:selected['trees']]:roots.append(emit(tree['tree_structure']))
    path=ROOT/'src/v10_tree_model.hpp'
    lines=['// Development-trained wire model; compact bytecode preserves double leaves.',
           '#pragma once','#include <array>','#include <cstdint>','namespace v10_tree_model {',
           'constexpr double blend=1.0;',
           f'constexpr std::array<uint32_t,{len(roots)}> roots={{{",".join(map(str,roots))}}};',
           f'constexpr std::array<uint8_t,{len(payload)}> code={{{{',
           *('  '+','.join(map(str,payload[i:i+48]))+',' for i in range(0,len(payload),48)),
           '}};','} // namespace v10_tree_model','']
    path.write_text('\n'.join(lines))
    result={'source':str(path),'source_bytes':path.stat().st_size,'nodes':node_count,'bytecode_bytes':len(payload),'threshold_policy':'greatest float32 not above original float64 threshold; exact for float32 features',
            'trees':len(roots),'python_validation_score':selected['oracle_score'],
            'holdout_used':False}
    (ROOT/'reports/V10-tree-export.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
