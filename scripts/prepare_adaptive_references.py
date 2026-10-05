"""Select reference queries using input geometry and frozen model outputs only."""
import csv,json
import numpy as np
from architecture import ROOT
from compare_architecture_ensembles import prediction

def main():
    phase,_=prediction('V27-minplus-neural.json','v27','plain');interval,_=prediction('V26-interval-minplus.json','v26','interval')
    folder=ROOT/'out/evaluation'
    with (folder/'validation.request.csv').open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==len(phase)==len(interval)
    def xy(pin):
        parts=pin.split('/')[0].split('_');return int(parts[1]),int(parts[2])
    short=np.array([sum(abs(a-b) for a,b in zip(xy(r['From']),xy(r['To'])))<25 for r in rows])
    uncertain=(np.abs(phase-interval)/np.maximum((phase+interval)/2,1)>.01)&~short
    for name,mask in [('validation.v33-short.request.csv',short),('validation.v34-uncertain.request.csv',uncertain)]:
        with (folder/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['From','To']);w.writeheader();w.writerows({k:r[k] for k in ['From','To']} for r,keep in zip(rows,mask) if keep)
    print(json.dumps({'short':int(short.sum()),'uncertain':int(uncertain.sum()),'golden_used_for_selection':False}))

if __name__=='__main__':main()
