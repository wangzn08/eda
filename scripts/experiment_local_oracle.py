"""Apply translated feasible-path upper bounds; fit no answer-dependent parameters."""
import argparse
import csv
import json
import mmap
import struct
import time
from architecture import Architecture,ROOT
from evaluate import metrics

class LocalOracle:
    def __init__(self,path):
        self.file=path.open('rb');self.data=mmap.mmap(self.file.fileno(),0,access=mmap.ACCESS_READ)
        if self.data[:8]!=b'LOCORC1\0':raise ValueError('Invalid local oracle magic')
        version,self.lx,self.ly,ns,nt,self.radius=struct.unpack_from('<6I',self.data,8)
        if version not in (1,2,4,5):raise ValueError('Unsupported oracle version')
        self.version=version
        self.ns,self.nt=ns,nt
        s=struct.unpack_from(f'<{ns}H',self.data,32)
        t=struct.unpack_from(f'<{nt}H',self.data,32+2*ns)
        self.sources={p:i for i,p in enumerate(s)};self.targets={p:i for i,p in enumerate(t)}
        self.offset=32+2*(ns+nt);self.width=2*self.lx+1
        self.stride=self.width*(2*self.ly+1)*nt
        if version==5:
            self.blocks=struct.unpack_from(f'<{ns+1}Q',self.data,self.offset)
            if self.blocks[0]!=self.offset+8*(ns+1) or self.blocks[-1]!=len(self.data):
                raise ValueError('Wrong dictionary offsets')
            for i in range(ns):
                size,=struct.unpack_from('<I',self.data,self.blocks[i])
                if size>65536 or self.blocks[i+1]-self.blocks[i]!=4+4*size+2*self.stride:
                    raise ValueError('Wrong dictionary size')
        elif len(self.data)!=self.offset+ns*self.stride*4:raise ValueError('Wrong oracle file size')
        self.arch=Architecture()

    def upper_bound(self,source,target):
        (sx,sy),sp,_=self.arch.pin(source);(tx,ty),tp,_=self.arch.pin(target)
        dx,dy=tx-sx,ty-sy
        if abs(dx)>self.lx or abs(dy)>self.ly:return None,'distance'
        si=self.sources.get(self.arch.port_ids[sp]);ti=self.targets.get(self.arch.port_ids[tp])
        if si is None or ti is None:return None,'port'
        local_index=((dy+self.ly)*self.width+dx+self.lx)*self.nt+ti
        index=si*self.stride+local_index
        if self.version in (4,5):
            if self.version==5:
                block=self.blocks[si];size,=struct.unpack_from('<I',self.data,block)
                entry,=struct.unpack_from('<H',self.data,block+4+4*size+2*local_index)
                if entry>=size:raise ValueError('Dictionary index out of range')
                packed,=struct.unpack_from('<I',self.data,block+4+4*entry)
            else:packed,=struct.unpack_from('<I',self.data,self.offset+4*index)
            cost=packed&16383;margin=(packed>>14)&65535
            if cost==16383:return None,'missing'
        else:
            cost,margin=struct.unpack_from('<HH',self.data,self.offset+4*index)
            if cost==65535:return None,'missing'
        if self.version==1:
            left=min(sx,tx)-(margin&15);right=max(sx,tx)+((margin>>4)&15)
            lower=min(sy,ty)-((margin>>8)&15);upper=max(sy,ty)+((margin>>12)&15)
            monotone_x=monotone_y=False
        elif self.version==2:
            left=min(sx,tx)-(margin&7);right=max(sx,tx)+((margin>>3)&7)
            lower=min(sy,ty)-((margin>>6)&7);upper=max(sy,ty)+((margin>>9)&7)
            monotone_x=bool(margin&(1<<12));monotone_y=bool(margin&(1<<13))
        else:
            left=min(sx,tx)-(margin&15);right=max(sx,tx)+((margin>>4)&15)
            lower=min(sy,ty)-((margin>>8)&15);upper=max(sy,ty)+((margin>>12)&15)
            monotone_x=bool(packed&(1<<30));monotone_y=bool(packed&(1<<31))
        if left<0 or lower<0 or right>=self.arch.width or upper>=self.arch.height:return None,'boundary'
        for block in self.arch.blocks:
            if left<=block['right'] and right>=block['left'] and lower<=block['upper'] and upper>=block['lower']:
                return None,'block'
        for line in self.arch.lines:
            lo,hi=(left,right) if line['direction']=='vertical' else (lower,upper)
            if lo<=line['site']<hi:
                monotone=monotone_x if line['direction']=='vertical' else monotone_y
                if not monotone:return None,'line'
                start,end=sorted((sx,tx) if line['direction']=='vertical' else (sy,ty))
                if start<=line['site']<end:cost+=line['delay']
                elif self.version in (4,5):cost+=2*line['delay']
        return cost,'hit'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stem',default='v6-pair')
    parser.add_argument('--split',choices=('development','validation'),default='validation')
    parser.add_argument('--oracle',default='out/local-oracle/regular-12.bin')
    parser.add_argument('--tag',default='local')
    args=parser.parse_args();start=time.monotonic()
    root=ROOT/'out/evaluation';oracle=LocalOracle(ROOT/args.oracle)
    with (root/f'{args.split}.golden.csv').open() as f,(root/f'{args.split}.{args.stem}.csv').open() as g:
        expected=list(csv.DictReader(f));baseline=list(csv.DictReader(g))
    if len(expected)!=len(baseline):raise ValueError('Row count mismatch')
    output=[];counts={};changed=0;violations=[];gold_hit=[];old_hit=[];new_hit=[]
    for i,(truth,pred) in enumerate(zip(expected,baseline)):
        if (truth['From'],truth['To'])!=(pred['From'],pred['To']):raise ValueError('Endpoint mismatch')
        bound,reason=oracle.upper_bound(truth['From'],truth['To'])
        counts[reason]=counts.get(reason,0)+1
        row=dict(pred)
        if bound is not None:
            if bound<int(truth['delay']):violations.append({'row':i,'bound':bound,'golden':int(truth['delay'])})
            row['delay']=str(min(int(pred['delay']),bound))
            changed+=row['delay']!=pred['delay']
            gold_hit.append(truth);old_hit.append(pred);new_hit.append(row)
        output.append(row)
    report={'split':args.split,'baseline':args.stem,'before':metrics(expected,baseline),
            'after':metrics(expected,output),'counts':counts,'changed_rows':changed,
            'upper_bound_violations':len(violations),'violation_examples':violations[:10],
            'hit_before':metrics(gold_hit,old_hit),'hit_after':metrics(gold_hit,new_hit),
            'oracle_bytes':len(oracle.data),'oracle_path':args.oracle,'oracle_version':oracle.version,
            'fit_used_golden':False,'holdout_used':False,
            'elapsed_seconds':time.monotonic()-start}
    report_path=ROOT/'reports'/f'V8-{args.tag}-oracle-{args.split}-{args.stem}.json'
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    if violations:raise ValueError('Invalid feasible-path upper bound; see report')
    path=root/f'{args.split}.{args.stem}-{args.tag}.csv'
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=('From','To','delay'));writer.writeheader();writer.writerows(output)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
