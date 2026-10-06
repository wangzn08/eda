"""Choose scaling from architecture-only held-out distance bands."""
import csv,json
from architecture import ROOT
with (ROOT/'out/architecture-benchmark/joint-generalization.csv').open() as f:rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
names=['none','full','clipped_min_ratio','clipped_product_ratio','clipped_fade_from_q1'];items=[]
for method,name in enumerate(names):
 selected=[r for r in rows if int(r['method'])==method and not(r['qx']==5 and r['qy']==6)]
 n=sum(r['rows'] for r in selected)
 items.append({'method':name,'held_distance_cases':int(n),'mean_absolute_error_ps':sum(r['mean_absolute_error_ps']*r['rows'] for r in selected)/n,'mean_signed_error_ps':sum(r['mean_signed_error_ps']*r['rows'] for r in selected)/n,'exact_fraction':sum(r['exact_fraction']*r['rows'] for r in selected)/n})
r={'architecture_only':True,'golden_labels_used':False,'anchor_excluded':[5,6],'source_indices':[0,80,159],'qx_grid':[1,3,5,7],'qy_grid':[2,4,6,8],'methods':items,'per_distance':rows,'scope':'Different geometric distance bands than patch anchor, sources included in architecture preprocessing; not unseen ports, physical-route certificates, validation score or timing.'}
(ROOT/'reports/V92-joint-generalization.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(items,indent=2))
