"""Distill architecture search values at route states, not request answers.

Only records belonging to development requests are fitted. Validation records
are evaluated after fitting; golden labels are never teacher training targets.
"""
import json, time
import numpy as np
import lightgbm as lgb
from architecture import ROOT, Architecture

DTYPE = np.dtype([('row','<u4'),('sx','<u2'),('sy','<u2'),
                  ('tx','<u2'),('ty','<u2'),('core','<u2'),('target','<u2'),
                  ('entry','<i4'),('base','<i4'),('expanded','<i4')])
arch = Architecture()
incoming = np.array([[n['delta x'], n['delta y'], n.get('delay',0)]
                     for n in arch.nets], np.float32)

def features(records):
    sx,sy,tx,ty,core,target = [records[k].astype(np.int32)
                             for k in ('sx','sy','tx','ty','core','target')]
    dx,dy=tx-sx,ty-sy
    ax,ay=np.abs(dx),np.abs(dy)
    qx=np.where(ax>29,(ax-20)//10,0)
    qy=np.where(ay>35,(ay-24)//12,0)
    rx=np.sign(dx)*(ax-qx*10); ry=np.sign(dy)*(ay-qy*12)
    base=records['base'].astype(np.float32)
    cross=(np.minimum(sx,tx)<76)&(np.maximum(sx,tx)>89)
    cols=[sx,sy,tx,ty,core,target,dx,dy,ax,ay,qx,qy,rx,ry,
          dx%10,dy%12,sy%100,ty%100,sx<16,tx<16,sy<100,ty<100,
          cross,np.minimum(sx,119-sx),np.minimum(tx,119-tx),
          np.minimum(sy,549-sy),np.minimum(ty,549-ty),
          np.minimum(sy%100,99-sy%100),np.minimum(ty%100,99-ty%100),
          (sx>=76)&(sx<=89),(tx>=76)&(tx<=89),
          core//20,core%20,target//8,target%8,base,base-125*qx-127*qy]
    return np.column_stack(cols+[incoming[core,j] for j in range(3)]).astype(np.float32)

def aggregate(records,values,local,count):
    result=local.astype(np.float64).copy()
    np.minimum.at(result,records['row'],records['entry']+values)
    assert len(result)==count and np.all(result<1e9)
    return np.rint(np.maximum(0,result))

def main():
    folder=ROOT/'out/v184'
    with (folder/'teacher.states').open('rb') as f:
        assert f.read(8)==b'BELLST01'; f.read(64)
        assert int.from_bytes(f.read(4),'little')==DTYPE.itemsize==28
    states=np.memmap(folder/'teacher.states',dtype=DTYPE,offset=76,mode='r')
    z=np.load(ROOT/'out/v125/fit-features.npz');n=len(z['y']);nv=len(z['yv'])
    local=np.fromfile(folder/'teacher.local',dtype='<i4');assert len(local)==n+nv
    ids=np.flatnonzero(states['row']<n)
    rng=np.random.default_rng(20261008)
    if len(ids)>1200000:ids=np.sort(rng.choice(ids,1200000,replace=False))
    train=states[ids];valid=states[states['row']>=n].copy()
    av=features(valid);a=features(train)
    delta=(train['expanded']-train['base']).astype(np.float32)
    weight=1000/np.maximum(train['expanded'],100)
    localv=local[n:];valid['row']-=n
    def score(p):return float(100*np.mean(1-np.tanh(4*np.abs(p-z['yv'])/z['yv'])))
    teacher=aggregate(valid,valid['expanded'],localv,nv)
    baseline=aggregate(valid,valid['base'],localv,nv)
    report={'state':'running','fit_scope':'development architecture teacher states only',
            'golden_used_for_fitting':False,'holdout_used':False,
            'state_count':len(states),'fit_state_count':len(train),
            'teacher_score':score(teacher),'base_score':score(baseline),
            'scope':'Route-state value distillation; native speed not yet measured','candidates':[]}
    print(json.dumps({k:v for k,v in report.items() if k!='candidates'}),flush=True)
    begin=time.monotonic()
    for name,leaves,trees in [('tree1',8191,1),('tree4',2047,4),('tree16',511,16)]:
        ds=lgb.Dataset(a,label=delta,weight=weight)
        model=lgb.train({'objective':'regression_l1','learning_rate':1 if trees==1 else .3,
                         'num_leaves':leaves,'max_depth':24,'min_data_in_leaf':60,
                         'num_threads':1,'verbosity':-1,'force_col_wise':True,
                         'deterministic':True,'seed':20261008},ds,num_boost_round=trees)
        model.save_model(str(folder/f'{name}.txt'))
        pred=aggregate(valid,valid['base']+model.predict(av,num_threads=1),localv,nv)
        np.save(folder/f'{name}.npy',pred)
        item={'name':name,'score':score(pred),'elapsed_seconds':time.monotonic()-begin}
        report['candidates'].append(item);print(json.dumps(item),flush=True)
        (ROOT/'reports/V184-bellman-student.json').write_text(json.dumps(report,indent=2)+'\n')
    report['state']='complete'
    (ROOT/'reports/V184-bellman-student.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
