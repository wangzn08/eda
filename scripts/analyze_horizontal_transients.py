"""Architecture-only horizontal growth audit with geometric extrapolation holdout."""
import json
import numpy as np
from architecture import ROOT
z=np.loadtxt(ROOT/'out/architecture-benchmark/v80-horizontal-transients.csv',delimiter=',',skiprows=1,dtype=np.int32)
values={(int(s),int(t),int(x),int(y)):int(v) for s,t,x,y,v in z}
rows=[]
for sign in (-1,1):
 for lo,hi in ((30,39),(40,49),(50,59),(60,69),(70,79)):
  errors={k:[] for k in ('anchor20_cheapest','anchor40_measured_slope')};delta=[]
  for s,t,x,y,value in z:
   if not lo<=abs(x)<=hi or np.sign(x)!=sign or value>=65535:continue
   r=(abs(int(x))-20)%10;q=(abs(int(x))-20-r)//10;key=(int(s),int(t));y=int(y)
   d20=values[(*key,sign*(20+r),y)];d30=values[(*key,sign*(30+r),y)];d40=values[(*key,sign*(40+r),y)]
   delta.append(int(value)-values[(*key,int(x)-sign*10,y)]-125)
   errors['anchor20_cheapest'].append(d20+q*125-int(value))
   if lo>=50:errors['anchor40_measured_slope'].append(d40+(q-2)*max(125,d40-d30)-int(value))
  entry={'sign':sign,'distance_band':[lo,hi],'exact_periodic_fraction':float(np.mean(np.array(delta)==0)),'methods':{}}
  for name,e in errors.items():
   if not e:continue
   a=np.array(e);entry['methods'][name]={'rows':len(a),'exact_fraction':float(np.mean(a==0)),'mean_abs_error_ps':float(np.mean(np.abs(a))),'max_abs_error_ps':int(np.max(np.abs(a)))}
  rows.append(entry)
r={'architecture_only':True,'golden_labels_used':False,'source_port_indices':[0,80,159],'targets':160,'vertical_offsets':[-35,-24,-12,0,12,24,35],'rows':len(z),'bands':rows,'scope':'Finite nominal radius112 graph. Measured slopes use20..49, evaluated beyond50. Not physical validation accuracy or path certificate.'}
(ROOT/'reports/V80-horizontal-transients.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
