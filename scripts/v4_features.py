"""Endpoint and official-architecture features for V4 residual experiments."""
import csv
from pathlib import Path

from architecture import Architecture, ROOT

NAMES = (
    'source_x','source_y','target_x','target_y','dx','dy','abs_dx','abs_dy',
    'manhattan','v3_delay','source_port','target_port','source_family','target_family',
    'x_sign','y_sign','source_x_mod10','target_x_mod10','source_y_mod12','target_y_mod12',
    'vertical_gap_delay','horizontal_gap_delay','route_class','route_detour',
    'forced_detour','source_projection','target_projection',
    'source_fixed','target_fixed','source_y_mod100','target_y_mod100',
)


class FeatureBuilder:
    def __init__(self):
        arch=Architecture()
        self.port_ids=arch.port_ids
        families=sorted({p['Name'].split('[',1)[0] if p['Name'].startswith('Z') else p['Name'][0]
                         for p in arch.ports})
        self.families={name:i for i,name in enumerate(families)}
        self.first={n['from']:(n['delta x'],n['delta y']) for n in arch.nets}
        self.last={n['to']:(n['delta x'],n['delta y']) for n in arch.nets}
        self.vlines=[g for g in arch.lines if g['direction']=='vertical']
        self.hlines=[g for g in arch.lines if g['direction']=='horizontal']

    def family(self,port):
        name=port.split('[',1)[0] if port.startswith('Z') else port[0]
        return self.families[name]

    def build(self,source,target,baseline):
        ss,sp=source.split('/',1);ts,tp=target.split('/',1)
        sx,sy=map(int,ss.split('_')[1:]);tx,ty=map(int,ts.split('_')[1:])
        dx,dy=tx-sx,ty-sy
        direct=abs(dx)+abs(dy)
        first=self.first.get(sp,(0,0));last=self.last.get(tp,(0,0))
        forced=(abs(first[0])+abs(first[1])+abs(last[0])+abs(last[1])
                +abs(dx-first[0]-last[0])+abs(dy-first[1]-last[1]))
        source_projection=first[0]*dx+first[1]*dy
        target_projection=last[0]*dx+last[1]*dy
        route=0;detour=0
        if min(sx,tx)<=89 and max(sx,tx)>=76:
            bs=sy//100 if sy<550 and sy%100<50 else -1
            bt=ty//100 if ty<550 and ty%100<50 else -1
            if bs>=0 or bt>=0:
                if bs!=bt:route=1
                else:
                    route=2;lower=bs*100;upper=lower+49
                    detour=min(9,max(0,min(sy-lower+ty-lower+2,2*upper-sy-ty+2)//10))
        xmin,xmax=sorted((sx,tx));ymin,ymax=sorted((sy,ty))
        vg=sum(g['delay'] for g in self.vlines if xmin<=g['site']<xmax)
        hg=sum(g['delay'] for g in self.hlines if ymin<=g['site']<ymax)
        return (sx,sy,tx,ty,dx,dy,abs(dx),abs(dy),direct,baseline,
                self.port_ids[sp],self.port_ids[tp],self.family(sp),self.family(tp),
                (dx>0)-(dx<0),(dy>0)-(dy<0),sx%10,tx%10,sy%12,ty%12,
                vg,hg,route,detour,max(0,forced-direct),source_projection,target_projection,
                int(sp in self.first),int(tp in self.last),sy%100,ty%100)


def load_split(split):
    import numpy as np
    root=ROOT/'out/evaluation'
    count={'development':700705,'validation':150053}[split]
    x=np.empty((count,len(NAMES)),dtype=np.float32)
    truth=np.empty(count,dtype=np.float32)
    baseline=np.empty(count,dtype=np.float32)
    builder=FeatureBuilder()
    with (root/f'{split}.golden.csv').open(newline='') as g, (root/f'{split}.v3-final.csv').open(newline='') as p:
        for index,(a,b) in enumerate(zip(csv.DictReader(g),csv.DictReader(p))):
            if (a['From'],a['To'])!=(b['From'],b['To']):
                raise ValueError(f'Request order differs at {index}')
            value=float(b['delay'])
            x[index]=builder.build(a['From'],a['To'],value)
            truth[index]=float(a['delay']);baseline[index]=value
    return x,truth,baseline


if __name__=='__main__':
    import numpy as np
    for split in ('development','validation'):
        x,truth,baseline=load_split(split)
        path=ROOT/'out/evaluation'/f'{split}.v4-features.npz'
        np.savez(path,x=x,truth=truth,baseline=baseline)
        print(split,x.shape,path,flush=True)
