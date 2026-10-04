#pragma once
#include "architecture_data.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

// Compressed records store translation-invariant feasible paths, not global distances.
class LocalPathOracle {
    std::vector<unsigned char> bytes;
    std::array<int,archdata::P> sources{},targets{};
    std::vector<uint64_t> blocks;
    uint32_t lx=0,ly=0,nt=0,version=0,groups=1,rows_per_group=0;
    std::vector<uint32_t> decoded;
    uint64_t stride=0;
    uint64_t read(size_t offset,unsigned count) const {
        if(offset>bytes.size() || count>bytes.size()-offset) throw std::runtime_error("Truncated path oracle");
        uint64_t value=0;
        for(unsigned i=0;i<count;++i) value|=uint64_t(bytes[offset+i])<<(8*i);
        return value;
    }
    uint32_t record(int si,int ti,int dx,int dy) const {
        uint32_t packed;
        if(version==7) {
            auto index=(uint64_t(dy+ly)*(2*lx+1)+dx+lx)*nt+ti;
            packed=decoded[si*stride+index];
        } else {
            auto group=(dy+ly)/rows_per_group;
            auto block=blocks[si*groups+group],palette=read(block,4);
            auto index=(uint64_t((dy+ly)%rows_per_group)*(2*lx+1)+dx+lx)*nt+ti;
            auto entry=read(block+4+4*palette+2*index,2);
            if(entry>=palette) throw std::runtime_error("Invalid path oracle index");
            packed=read(block+4+4*entry,4);
        }
        return packed;
    }
public:
    explicit LocalPathOracle(const std::string& path) {
        std::ifstream file(path,std::ios::binary|std::ios::ate);
        if(!file) throw std::runtime_error("Cannot open path oracle");
        auto size=file.tellg();
        if(size<32 || size>100000000) throw std::runtime_error("Invalid path oracle size");
        bytes.resize(static_cast<size_t>(size));file.seekg(0);
        if(!file.read(reinterpret_cast<char*>(bytes.data()),size)) throw std::runtime_error("Cannot read path oracle");
        const unsigned char magic[8]={'L','O','C','O','R','C','1',0};
        if(!std::equal(magic,magic+8,bytes.begin())) throw std::runtime_error("Unsupported path oracle");
        version=read(8,4);
        if(version!=5 && version!=6 && version!=7) throw std::runtime_error("Unsupported path oracle version");
        lx=read(12,4);ly=read(16,4);auto ns=read(20,4);nt=read(24,4);
        if(lx>64 || ly>64 || ns==0 || ns>archdata::P || nt==0 || nt>archdata::P) throw std::runtime_error("Invalid path oracle dimensions");
        sources.fill(-1);targets.fill(-1);
        for(uint32_t i=0;i<ns+nt;++i) {
            auto p=read(32+2*i,2);
            if(p>=archdata::P) throw std::runtime_error("Invalid path oracle port");
            auto& map=i<ns?sources:targets;
            if(map[p]!=-1) throw std::runtime_error("Duplicate path oracle port");
            map[p]=i<ns?i:i-ns;
        }
        stride=uint64_t(2*lx+1)*(2*ly+1)*nt;
        size_t offset=32+2*(ns+nt);
        groups=version==6?4:1;rows_per_group=(2*ly+groups)/groups;
        if(version==7) {
            if(ns*stride>200000000) throw std::runtime_error("Decoded path oracle exceeds memory budget");
            decoded.resize(ns*stride);
            size_t position=offset;uint64_t sites=(2*lx+1)*(2*ly+1);
            auto varint=[&](size_t end) {
                uint32_t value=0;
                for(unsigned shift=0;shift<=4 && position<end;++shift) {
                    auto byte=bytes[position++];value|=uint32_t(byte&127)<<(shift*7);
                    if(byte<128) return value;
                    if(shift==4) break;
                }
                throw std::runtime_error("Invalid path oracle varint");
            };
            for(size_t si=0;si<ns;++si) for(size_t ti=0;ti<nt;++ti) {
                auto nc=read(position,4),nm=read(position+4,4);position+=8;
                if(nc>bytes.size()-position || nm>bytes.size()-position-nc) throw std::runtime_error("Truncated path plane");
                size_t end=position+nc;int64_t cost=0;
                for(size_t site=0;site<sites;++site) {
                    uint32_t z=varint(end);cost+=(z&1)?-int64_t((uint64_t(z)+1)/2):int64_t(z/2);
                    if(cost<0 || cost>16383) throw std::runtime_error("Invalid decoded path cost");
                    decoded[si*stride+site*nt+ti]=cost;
                }
                if(position!=end) throw std::runtime_error("Cost plane length mismatch");
                end+=nm;size_t site=0;
                while(position<end) {
                    auto run=varint(end),meta=varint(end);
                    if(run==0 || run>sites-site || meta>=(1u<<18)) throw std::runtime_error("Invalid footprint run");
                    for(size_t j=0;j<run;++j) decoded[si*stride+(site+j)*nt+ti]|=meta<<14;
                    site+=run;
                }
                if(site!=sites) throw std::runtime_error("Footprint plane length mismatch");
            }
            if(position!=bytes.size()) throw std::runtime_error("Trailing path oracle data");
            std::vector<unsigned char>().swap(bytes);
        } else {
            blocks.resize(ns*groups+1);
            for(size_t i=0;i<blocks.size();++i) blocks[i]=read(offset+8*i,8);
            if(blocks.front()!=offset+8*(ns*groups+1) || blocks.back()!=bytes.size()) throw std::runtime_error("Invalid path oracle offsets");
            for(size_t i=0;i<ns*groups;++i) {
                auto palette=read(blocks[i],4);
                uint64_t count=uint64_t(2*lx+1)*nt*std::min(rows_per_group,2*ly+1-uint32_t(i%groups)*rows_per_group);
                if(palette==0 || palette>65536 || blocks[i+1]<blocks[i] || blocks[i+1]-blocks[i]!=4+4*palette+2*count) throw std::runtime_error("Invalid path oracle dictionary");
            }
        }
    }
    uint64_t nominal_cost(int source_port,int target_port,int dx,int dy) const {
        if(dx < -int(lx) || dx>int(lx) || dy < -int(ly) || dy>int(ly) || sources[source_port]<0 || targets[target_port]<0) return std::numeric_limits<uint64_t>::max();
        auto cost=record(sources[source_port],targets[target_port],dx,dy)&16383;
        return cost==16383?std::numeric_limits<uint64_t>::max():cost;
    }
    uint64_t upper_bound(uint32_t source,uint32_t target) const {
        constexpr uint64_t missing=std::numeric_limits<uint64_t>::max();
        auto s=archdata::SITES[source/archdata::P],t=archdata::SITES[target/archdata::P];
        int dx=t.x-s.x,dy=t.y-s.y;
        if(dx < -int(lx) || dx>int(lx) || dy < -int(ly) || dy>int(ly)) return missing;
        int si=sources[source%archdata::P],ti=targets[target%archdata::P];
        if(si<0) return missing;
        if(ti<0) {
            uint64_t best=source==target?0:missing;
            for(const auto& arc:archdata::ARCS) if(arc.to==int(target%archdata::P)) {
                if(source/archdata::P==target/archdata::P && arc.from==int(source%archdata::P)) best=std::min(best,uint64_t(arc.delay));
                if(targets[arc.from]>=0) {
                    auto bound=upper_bound(source,(target/archdata::P)*archdata::P+arc.from);
                    if(bound!=missing) best=std::min(best,bound+arc.delay);
                }
            }
            return best;
        }
        uint32_t packed=record(si,ti,dx,dy);
        return translated_bound(s,t,packed);
    }
    static uint64_t translated_bound(archdata::XY s,archdata::XY t,uint32_t packed) {
        constexpr uint64_t missing=std::numeric_limits<uint64_t>::max();
        uint64_t cost=packed&16383;
        if(cost==16383) return missing;
        int left=std::min(s.x,t.x)-((packed>>14)&15),right=std::max(s.x,t.x)+((packed>>18)&15);
        int lower=std::min(s.y,t.y)-((packed>>22)&15),upper=std::max(s.y,t.y)+((packed>>26)&15);
        if(left<0 || lower<0 || right>=archdata::WIDTH || upper>=archdata::HEIGHT) return missing;
        for(const auto& b:archdata::BLOCKS) if(left<=b.right && right>=b.left && lower<=b.upper && upper>=b.lower) return missing;
        for(const auto& line:archdata::LINES) {
            int lo=line.vertical?left:lower,hi=line.vertical?right:upper;
            if(lo<=line.site && line.site<hi) {
                if(!(packed&(uint32_t(1)<<(line.vertical?30:31)))) return missing;
                int start=line.vertical?std::min(s.x,t.x):std::min(s.y,t.y);
                int end=line.vertical?std::max(s.x,t.x):std::max(s.y,t.y);
                cost+=line.delay*((start<=line.site && line.site<end)?1:2);
            }
        }
        return cost;
    }
};
