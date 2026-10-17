"""Per-core decision policies fitted to development architecture-search actions."""
import json,lzma,struct,time,hashlib
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from architecture import ROOT
from experiment_bellman_student import DTYPE,features

def main():
    folder=ROOT/'out/v185'
    with (folder/'teacher.states').open('rb') as f:
        assert f.read(8)==b'BELLST01';arch_hash=f.read(64)
        assert int.from_bytes(f.read(4),'little')==28
    records=np.memmap(folder/'teacher.states',dtype=DTYPE,offset=76,mode='r')
    actions=np.memmap(folder/'teacher.actions',dtype='<u2',mode='r')
    assert len(actions)==len(records)
    n=len(np.load(ROOT/'out/v125/fit-features.npz')['y'])
    rng=np.random.default_rng(20261008)
    train=np.flatnonzero((records['row']<n)&(actions<496))
    if len(train)>2400000:train=np.sort(rng.choice(train,2400000,replace=False))
    valid=np.flatnonzero((records['row']>=n)&(actions<496))
    # Baseline cost features are excluded: selecting an action must not require
    # evaluating the previous search/response model first.
    columns=list(range(35))+[37,38,39]
    begin=time.monotonic();report={'state':'running','fit_scope':'development architecture actions only',
        'golden_used_for_fitting':False,'holdout_used':False,'training_states':len(train),
        'validation_states':len(valid),'feature_columns':columns,'candidates':[]}
    for name,leaves,minleaf in [('small',511,20),('wide',2047,8)]:
        directories=[];nodes=bytearray();probes=bytearray();correct=top2correct=count=0
        for core in range(160):
            ti=train[records['core'][train]==core];vi=valid[records['core'][valid]==core]
            offset=len(nodes)//16
            if not len(ti):directories.append((offset,0));continue
            a=features(records[ti])[:,columns];av=features(records[vi])[:,columns]
            tree=DecisionTreeClassifier(max_leaf_nodes=leaves,max_depth=24,
                 min_samples_leaf=minleaf,random_state=20261008)
            tree.fit(a,actions[ti]);t=tree.tree_;classes=tree.classes_
            leaf_actions={}
            for j in range(t.node_count):
                if t.children_left[j]<0:
                    counts=t.value[j,0];order=np.argsort(-counts,kind='stable')
                    first=int(classes[order[0]]);second=int(classes[order[1]]) if len(order)>1 else first
                    confidence=int(round(255*(counts[order[0]]-(counts[order[1]] if len(order)>1 else 0))/counts.sum()))
                    leaf_actions[j]=(first,second,confidence)
                    nodes.extend(struct.pack('<iihBBHH',-1,-1,0,255,confidence,first,second))
                else:
                    threshold=int(np.floor(t.threshold[j]));assert -32768<=threshold<=32767
                    nodes.extend(struct.pack('<iihBBHH',int(t.children_left[j]),int(t.children_right[j]),threshold,int(t.feature[j]),0,0,0))
            directories.append((offset,t.node_count))
            if len(vi):
                picked=np.array([leaf_actions[j][:2] for j in tree.apply(av)],np.uint16)
                correct+=int(np.sum(picked[:,0]==actions[vi]));top2correct+=int(np.sum(np.any(picked==actions[vi,None],axis=1)));count+=len(vi)
                for row,leaf in zip(records[vi[:64]],tree.apply(av[:64])):
                    first,second,confidence=leaf_actions[leaf]
                    probes.extend(struct.pack('<6H2HBB',*[int(row[k]) for k in ('sx','sy','tx','ty','core','target')],first,second,confidence,0))
        index=b''.join(struct.pack('<II',*d) for d in directories)
        header=b'PPOLICY1'+arch_hash+struct.pack('<III',38,160,len(index)+len(nodes))
        encoded=lzma.compress(index+nodes,preset=6)
        path=folder/f'{name}.bin';path.write_bytes(header+encoded)
        (folder/f'{name}.parity').write_bytes(probes)
        item={'name':name,'action_accuracy':correct/count,'top2_action_accuracy':top2correct/count,
              'model_bytes':path.stat().st_size,'decoded_bytes':len(index)+len(nodes),
              'elapsed_seconds':time.monotonic()-begin,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        report['candidates'].append(item);print(json.dumps(item),flush=True)
        (ROOT/'reports/V185-prefix-policy-training.json').write_text(json.dumps(report,indent=2)+'\n')
    report['state']='complete';(ROOT/'reports/V185-prefix-policy-training.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
