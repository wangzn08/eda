"""Analyze development-only exact route traces against V2/V3 estimates."""
import collections
import csv
import json

from architecture import ROOT
from experiment_displacement import weighted_score
from prepare_route_sample import bucket


def rows(name):
    with (ROOT/'out/evaluation'/name).open(newline='') as f:
        return list(csv.DictReader(f))


def summary(items):
    n=len(items)
    if not n:return None
    return {'rows':n,'v2_score':sum(x['v2_score'] for x in items)/n,
            'v3_score':sum(x['v3_score'] for x in items)/n,
            'mean_detour':sum(x['detour'] for x in items)/n,
            'detour_fraction':sum(x['detour']>0 for x in items)/n,
            'mean_turns':sum(x['turns'] for x in items)/n,
            'mean_long_hops':sum(x['long_hops'] for x in items)/n}


def main():
    golden=rows('route-v3-development.golden.csv')
    exact=rows('route-v3-development.exact.csv')
    v2=rows('route-v3-development.v2.csv')
    trace=rows('route-v3-development.trace.csv')
    if not len(golden)==len(exact)==len(v2)==len(trace)==600:
        raise ValueError('Missing route records')
    groups=collections.defaultdict(list)
    all_items=[]
    for i,(a,b,c,d) in enumerate(zip(golden,exact,v2,trace)):
        if (a['From'],a['To'])!=(b['From'],b['To']) or a['delay']!=b['delay'] or int(d['row'])!=i+1:
            raise ValueError('Exact route and answer mismatch')
        truth,estimated=int(a['delay']),int(c['delay'])
        detour,turns,long_hops=int(d['detour']),int(d['turns']),int(d['long_hops'])
        item={'v2_score':weighted_score(truth,estimated),'v3_score':None,
              'detour':detour,'turns':turns,'long_hops':long_hops}
        all_items.append(item)
        groups[('distance',bucket(a))].append(item)
        groups[('detour','zero' if detour==0 else '1-10' if detour<=10 else '11+')].append(item)
        groups[('turns','0-1' if turns<=1 else '2-3' if turns<=3 else '4+')].append(item)
    result={'exact_matches':len(golden),'exact_cpu_seconds':461.327,
            'overall_v2':sum(x['v2_score'] for x in all_items)/len(all_items),
            'note':'Sample is deliberately distance-stratified development data, not representative of the hidden request mix.'}
    path=ROOT/'out/evaluation/route-v3-development.v3.csv'
    if not path.exists():
        raise ValueError('Generate route-v3-development.v3.csv before analysis')
    v3=rows(path.name)
    if len(v3)!=len(golden):
        raise ValueError('V3 route prediction count differs')
    for item,a,c in zip(all_items,golden,v3):
        item['v3_score']=weighted_score(int(a['delay']),int(c['delay']))
    result['overall_v3']=sum(x['v3_score'] for x in all_items)/len(all_items)
    result['groups']={kind:{key:summary(value) for (k,key),value in groups.items() if k==kind}
                      for kind in ('distance','detour','turns')}
    (ROOT/'reports/V3-exact-route-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
