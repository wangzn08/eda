"""Lossless cost-delta/footprint-run encoding; decode once before requests."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
from architecture import ROOT

def varint(value):
    result=bytearray()
    while value>=128:result.append((int(value)&127)|128);value=int(value)>>7
    result.append(int(value));return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();source=ROOT/a.input;target=ROOT/a.output
    if source==target:raise ValueError('Distinct paths required')
    with source.open('rb') as f:
        magic=f.read(8);header=list(struct.unpack('<6I',f.read(24)));ports=f.read(2*(header[3]+header[4]))
    if magic!=b'LOCORC1\0' or header[0]!=4:raise ValueError('Raw version 4 required')
    _,lx,ly,ns,nt,r=header;sites=(2*lx+1)*(2*ly+1)
    data=np.memmap(source,dtype='<u4',offset=32+2*(ns+nt),shape=(ns,sites,nt),mode='r')
    header[0]=7;cost_bytes=meta_bytes=0
    tmp=target.with_suffix(target.suffix+'.tmp')
    with tmp.open('wb') as f:
        f.write(magic);f.write(struct.pack('<6I',*header));f.write(ports)
        for source_row in data:
            for ti in range(nt):
                plane=source_row[:,ti];cost=(plane&16383).astype(np.int32)
                delta=np.diff(cost,prepend=0);zigzag=np.where(delta>=0,2*delta,-2*delta-1)
                costs=bytearray()
                for value in zigzag:costs.extend(varint(value))
                meta=plane>>14;starts=np.r_[0,np.flatnonzero(meta[1:]!=meta[:-1])+1];ends=np.r_[starts[1:],len(meta)]
                runs=bytearray()
                for start,end in zip(starts,ends):runs.extend(varint(end-start));runs.extend(varint(meta[start]))
                f.write(struct.pack('<2I',len(costs),len(runs)));f.write(costs);f.write(runs)
                cost_bytes+=len(costs);meta_bytes+=len(runs)
    tmp.replace(target)
    report={'encoding':'target-plane signed cost deltas plus footprint runs; decode once to uint32 records',
      'input':a.input,'output':a.output,'raw_bytes':source.stat().st_size,'compressed_bytes':target.stat().st_size,
      'decoded_payload_bytes':data.size*4,'cost_bytes':cost_bytes,'footprint_bytes':meta_bytes,
      'fit_used_golden':False,'holdout_used':False,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (ROOT/'reports'/f'V9-plane-compression-{lx}-{ly}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
