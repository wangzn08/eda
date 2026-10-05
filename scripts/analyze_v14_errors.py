"""Describe validation error concentration without opening holdout labels."""
import csv,json,math
from collections import defaultdict
from architecture import ROOT

def main():
    root=ROOT/'out/evaluation';groups=defaultdict(lambda:[0,0.,0.,0,0,0]);worst=[]
    with (root/'validation.golden.csv').open() as f,(ROOT/'out/acceptance-v14/validation.csv').open() as g,(root/'validation.v13-bound.csv').open() as h:
        for a,b,c in zip(csv.DictReader(f),csv.DictReader(g),csv.DictReader(h)):
            assert (a['From'],a['To'])==(b['From'],b['To'])==(c['From'],c['To'])
            y,p,u=int(a['delay']),int(b['delay']),int(c['delay']);sx,sy=map(int,a['From'].split('/')[0].split('_')[1:]);tx,ty=map(int,a['To'].split('/')[0].split('_')[1:]);d=abs(tx-sx)+abs(ty-sy)
            e=abs(p-y)/max(y,1);loss=100*math.tanh(4*e)
            for key in ('all','bound:'+str(u<100000000),'distance:'+('short' if d<25 else 'medium' if d<150 else 'long'),'source:'+a['From'].split('/')[1].split('[')[0],'target:'+a['To'].split('/')[1].split('[')[0]):
                v=groups[key];v[0]+=1;v[1]+=loss;v[2]+=e;v[3]+=p<y;v[4]+=p>y;v[5]+=p==y
            worst.append({'From':a['From'],'To':a['To'],'golden':y,'predicted':p,'upper':u,'relative_error':e})
    rows=[{'group':k,'rows':v[0],'score':100-v[1]/v[0],'mean_relative_error':v[2]/v[0],'loss_sum':v[1],'under':v[3],'over':v[4],'exact':v[5]} for k,v in groups.items()]
    rows.sort(key=lambda z:z['loss_sum'],reverse=True)
    report={'split':'validation','holdout_used':False,'groups':rows,'worst':sorted(worst,key=lambda z:z['relative_error'],reverse=True)[:50]}
    (ROOT/'reports/V16-error-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(rows[:14],indent=2),flush=True)

if __name__=='__main__':main()
