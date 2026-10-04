"""Losslessly replace packed witnesses by per-source 16-bit dictionary indices."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
from architecture import ROOT

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--y-groups',type=int,choices=(1,4),default=1)
    args=parser.parse_args();source=ROOT/args.input;target=ROOT/args.output
    if source==target:raise ValueError('Distinct files required')
    with source.open('rb') as f:
        magic=f.read(8);header=list(struct.unpack('<6I',f.read(24)))
        if magic!=b'LOCORC1\0' or header[0]!=4:raise ValueError('Version 4 raw oracle required')
        _,lx,ly,ns,nt,radius=header;ports=f.read(2*(ns+nt))
    offset=32+2*(ns+nt);stride=(2*lx+1)*(2*ly+1)*nt
    data=np.memmap(source,dtype='<u4',mode='r',offset=offset,shape=(ns,stride))
    offsets=[];counts=[];header[0]=5 if args.y_groups==1 else 6
    groups=args.y_groups;rows=(2*ly+groups)//groups
    chunks=[row[a*(2*lx+1)*nt:min(a+rows,2*ly+1)*(2*lx+1)*nt] for row in data for a in range(0,2*ly+1,rows)]
    if len(chunks)!=ns*groups:raise ValueError("Unsupported number of groups")
    with target.open('wb') as f:
        f.write(magic);f.write(struct.pack('<6I',*header));f.write(ports)
        table_offset=f.tell();f.write(b'\0'*(8*(ns*groups+1)))
        for row in chunks:
            palette,indices=np.unique(row,return_inverse=True)
            if len(palette)>65536:raise ValueError('Source dictionary exceeds 16-bit capacity')
            offsets.append(f.tell());counts.append(len(palette))
            f.write(struct.pack('<I',len(palette)))
            f.write(palette.astype('<u4').tobytes());f.write(indices.astype('<u2').tobytes())
        offsets.append(f.tell());f.seek(table_offset);f.write(struct.pack(f'<{ns*groups+1}Q',*offsets))
    report={'input':args.input,'output':args.output,'raw_bytes':source.stat().st_size,
            'compressed_bytes':target.stat().st_size,'max_dictionary_entries':max(counts),
            'dictionary_entries':sum(counts),'entries':ns*stride,
            'encoding':'per-source uint16 index into uint32 path-witness dictionary',
            'fit_used_golden':False,'holdout_used':False,'y_groups':groups,
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (ROOT/'reports'/f'V8-compression-{lx}-{ly}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
