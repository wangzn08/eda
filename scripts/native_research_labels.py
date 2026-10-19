"""Development/validation labels without depending on historical feature fits."""
import csv
import numpy as np
from architecture import ROOT

def load_labels():
 cache=ROOT/'out/v125/fit-features.npz'
 if cache.exists():
  with np.load(cache) as z:return {'y':z['y'].copy(),'yv':z['yv'].copy()}
 result={}
 for split,key in [('development','y'),('validation','yv')]:
  with (ROOT/f'out/evaluation/{split}.golden.csv').open() as stream:
   result[key]=np.fromiter((int(row['delay']) for row in csv.DictReader(stream)),dtype=np.int64)
 return result
