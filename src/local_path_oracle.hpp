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

// Version 5 stores translation-invariant feasible paths, not global distances.
class LocalPathOracle {
    std::vector<unsigned char> bytes;
    std::array<int,archdata::P> sources{},targets{};
    std::vector<uint64_t> blocks;
    uint32_t lx=0,ly=0,nt=0;
    uint64_t stride=0;
    uint64_t read(size_t offset,unsigned count) const {
        if(offset>bytes.size() || count>bytes.size()-offset) throw std::runtime_error("Truncated path oracle");
        uint64_t value=0;
        for(unsigned i=0;i<count;++i) value|=uint64_t(bytes[offset+i])<<(8*i);
        return value;
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
        if(!std::equal(magic,magic+8,bytes.begin()) || read(8,4)!=5) throw std::runtime_error("Unsupported path oracle");
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
        auto offset=32+2*(ns+nt);blocks.resize(ns+1);
        for(size_t i=0;i<blocks.size();++i) blocks[i]=read(offset+8*i,8);
        if(blocks.front()!=offset+8*(ns+1) || blocks.back()!=bytes.size()) throw std::runtime_error("Invalid path oracle offsets");
        for(size_t i=0;i<ns;++i) {
            auto palette=read(blocks[i],4);
            if(palette==0 || palette>65536 || blocks[i+1]<blocks[i] || blocks[i+1]-blocks[i]!=4+4*palette+2*stride) throw std::runtime_error("Invalid path oracle dictionary");
        }
    }
    uint64_t upper_bound(uint32_t source,uint32_t target) const {
        constexpr uint64_t missing=std::numeric_limits<uint64_t>::max();
        auto s=archdata::SITES[source/archdata::P],t=archdata::SITES[target/archdata::P];
        int dx=t.x-s.x,dy=t.y-s.y;
        if(dx < -int(lx) || dx>int(lx) || dy < -int(ly) || dy>int(ly)) return missing;
        int si=sources[source%archdata::P],ti=targets[target%archdata::P];
        if(si<0 || ti<0) return missing;
        auto block=blocks[si],palette=read(block,4);
        auto index=(uint64_t(dy+ly)*(2*lx+1)+dx+lx)*nt+ti;
        auto entry=read(block+4+4*palette+2*index,2);
        if(entry>=palette) throw std::runtime_error("Invalid path oracle index");
        uint32_t packed=read(block+4+4*entry,4);
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
