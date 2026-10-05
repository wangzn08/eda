"""Development path compression probe; no predictor or validation fitting."""
import csv,json,collections
import numpy as np
from architecture import ROOT
with (ROOT/'out/evaluation/v62-skeleton.states.csv').open() as f:
    groups=collections.defaultdict(list)
    for r in csv.DictReader(f):groups[int(r['row'])].append({k:int(v) for k,v in r.items()})
with (ROOT/'out/evaluation/route-v3-development.golden.csv').open() as f:gold=list(csv.DictReader(f))[::25][:24]
assert len(groups)==len(gold)==24
items=[];total=compressed=0;patterns=collections.Counter()
for row,states in sorted(groups.items()):
    assert states[0]['delay']==int(gold[row-1]['delay'])
    edges=[(a['port'],b['port'],b['x']-a['x'],b['y']-a['y']) for a,b in zip(states,states[1:])]
    i=0;tokens=0;repeated=0
    while i<len(edges):
        choice=(1,1)
        for length in range(1,min(4,len(edges)-i)+1):
            n=1
            while edges[i+n*length:i+(n+1)*length]==edges[i:i+length]:n+=1
            if n>1 and (n-1)*length>(choice[1]-1)*choice[0]:choice=(length,n)
        length,n=choice;tokens+=length;repeated+=(n-1)*length
        if n>1:patterns[tuple(edges[i:i+length])]+=n
        i+=length*n
    total+=len(edges);compressed+=tokens
    items.append({'row':row,'delay':states[0]['delay'],'transitions':len(edges),
                  'compressed_transition_tokens':tokens,'repeated_transitions':repeated})
report={'split':'distance_stratified_development_sample','rows':24,'holdout_used':False,
        'exact_delay_matches':24,'transitions':total,'compressed_transition_tokens':compressed,
        'token_reduction_fraction':1-compressed/total,
        'frequent_repeated_patterns':[{'transitions':p,'occurrences':n} for p,n in patterns.most_common(12)],
        'queries':items,'process_log':(ROOT/'out/v62-skeleton.log').read_text(),
        'scope':'Greedy exact repeated transition patterns of length1..4; token count excludes repetition metadata. Small stratified sample, not throughput or compression-size proof.'}
(ROOT/'reports/V62-path-skeleton-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('queries','process_log','frequent_repeated_patterns')},indent=2))
