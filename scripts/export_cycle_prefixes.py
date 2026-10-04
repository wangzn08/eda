"""Compile a tiny architecture-derived bank of source-to-long-wire witnesses."""
import json,struct
import numpy as np
from architecture import Architecture,ROOT

def main():
    path=ROOT/'out/local-oracle/factorized-20-v4.bin'
    with path.open('rb') as f:
        if f.read(8)!=b'LOCORC1\0':raise ValueError('Bad magic')
        version,lx,ly,ns,nt,r=struct.unpack('<6I',f.read(24))
        if version!=4:raise ValueError('Raw witness table required')
        sources=struct.unpack(f'<{ns}H',f.read(2*ns));targets=struct.unpack(f'<{nt}H',f.read(2*nt))
    arch=Architecture();longs={arch.port_ids[n['to']] for n in arch.nets if abs(n['delta x'])+abs(n['delta y'])>=10}
    sites=(2*lx+1)*(2*ly+1);data=np.memmap(path,dtype='<u4',offset=32+2*(ns+nt),shape=(ns,sites,nt),mode='r')
    indices=np.arange(sites);dx=indices%(2*lx+1)-lx;dy=indices//(2*lx+1)-ly;records=[]
    for si,sp in enumerate(sources):
        for ti,tp in enumerate(targets):
            if tp not in longs:continue
            packed=data[si,:,ti];cost=packed&16383
            order=np.lexsort((abs(dx)+abs(dy),cost));chosen=[]
            for index in order:
                if cost[index]==16383:break
                if any(abs(int(dx[index]-dx[j]))+abs(int(dy[index]-dy[j]))<4 for j in chosen):continue
                chosen.append(index);records.append((sp,tp,int(dx[index]),int(dy[index]),int(packed[index])))
                if len(chosen)==4:break
    out=ROOT/'src/cycle_prefix_bank.hpp'
    out.write_text('// Architecture-derived entry-path witnesses; no delay labels used.\n#pragma once\n#include <array>\n#include <cstdint>\nnamespace cycle_prefix_bank {\nstruct Entry {uint16_t source,target;int8_t dx,dy;uint32_t packed;};\nconstexpr std::array<Entry,'+str(len(records))+'> entries={{\n'+''.join('  {'+','.join(map(str,r))+'},\n' for r in records)+'}};\n}\n')
    report={'records':len(records),'source_bytes':out.stat().st_size,'runtime_record_bytes':12*len(records),
       'selection':'up to 4 low-cost spatially separated witnesses per source/long-input pair',
       'fit_used_golden':False,'holdout_used':False,'input':str(path.relative_to(ROOT))}
    (ROOT/'reports/V13-prefix-bank.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
