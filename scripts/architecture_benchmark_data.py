"""Cache only development/validation architecture features for challenger models."""
import numpy as np
from architecture import ROOT
from experiment_v19_route_bound import improved_data

def load(split):
    assert split in ('development','validation')
    folder=ROOT/'out/architecture-benchmark';folder.mkdir(exist_ok=True)
    path=folder/f'{split}.npz'
    if path.exists():
        z=np.load(path);return z['x'],z['y'],z['b'],z['u']
    x,y,b,u=improved_data(split);np.savez(path,x=x,y=y,b=b,u=u);return x,y,b,u
