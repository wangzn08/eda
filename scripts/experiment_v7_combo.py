"""Combine endpoint direction and region residuals after V6."""
import json
from architecture import ROOT
from experiment_region_port import load
import experiment_v6_port_pair as pair
import experiment_v4_interactions as geom

def methods(kind):return pair if kind.startswith('pair_') else geom
def apply(rows,kind,table):
    module=methods(kind)
    return [(*r[:7],max(0,round(r[7]+table.get(module.key(r,kind),0)))) for r in rows]

def main():
    dev,val=load('development','v6-pair'),load('validation','v6-pair')
    orders=(('pair_signs','route_dy20','route_source_yphase','route_target_yphase'),
            ('route_dy20','route_source_yphase','route_target_yphase','pair_signs'),
            ('pair_ysign','pair_xsign','route_dy20','route_source_yphase','route_target_yphase'),
            ('pair_signs','route_dy20','route_source_x','route_target_x'))
    results=[]
    for order in orders:
        d,v=dev,val;stages=[]
        for kind in order:
            module=methods(kind);table=module.fit(d,kind,20)
            d,v=apply(d,kind,table),apply(v,kind,table)
            stages.append({'kind':kind,'entries':len(table),'validation_score':geom.score(v,'signed_dy_exact',{})})
        item={'order':order,'stages':stages};results.append(item);print(item,flush=True)
    (ROOT/'reports/V7-combo-research.json').write_text(json.dumps({'candidates':results,'holdout_used':False},indent=2)+'\n')

if __name__=='__main__':main()
