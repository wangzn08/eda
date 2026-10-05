#pragma once
#include "architecture_data.hpp"
#include "potential_lower_model.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

// Pattern database of a relaxed periodic routing graph, not request answers.
class PhaseLowerBound {
    struct Group {unsigned px=0,patterns=0,width=0;std::vector<int16_t> base;std::vector<uint32_t> ids;std::vector<uint16_t> values;};
    std::array<Group,2> groups;
    std::array<int,archdata::P> input_index;

    std::array<uint64_t,archdata::WIDTH> xgap{};
    std::array<uint64_t,archdata::HEIGHT> ygap{};
public:
    explicit PhaseLowerBound(const std::string& path) {
        std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("Cannot open phase bounds");
        auto read=[&](void* p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated phase bounds");};
        char magic[8],hash[64];read(magic,8);read(hash,64);
        if(std::string(magic,8)!="PHASELB4" || std::string(hash,64)!=archdata::HASH)throw std::runtime_error("Phase bounds architecture mismatch");
        uint32_t header[6];read(header,sizeof(header));if(header[0]!=1 || header[1]!=archdata::P || header[2]!=160 || header[3]!=4 || header[4]!=10 || header[5]!=12)throw std::runtime_error("Invalid phase bound dimensions");
        input_index.fill(-1);std::array<uint16_t,160> ports;read(ports.data(),ports.size()*2);
        for(size_t i=0;i<ports.size();++i){if(ports[i]>=archdata::P || input_index[ports[i]]>=0)throw std::runtime_error("Invalid phase ports");input_index[ports[i]]=int(i);}
        size_t count=4*archdata::P*160;auto& g=groups[1];
        uint32_t info[3];read(info,sizeof(info));g.px=info[0];g.patterns=info[1];g.width=info[2];
        if(g.px!=10 || g.patterns==0 || g.patterns>count || (g.width!=2 && g.width!=4))throw std::runtime_error("Invalid phase dictionary");
        g.base.resize(count);g.ids.resize(count);read(g.base.data(),count*2);
        if(g.width==2){std::vector<uint16_t> ids(count);read(ids.data(),count*2);std::copy(ids.begin(),ids.end(),g.ids.begin());}else read(g.ids.data(),count*4);
        for(auto id:g.ids)if(id>=g.patterns)throw std::runtime_error("Invalid phase pattern index");
        uint64_t bytes;read(&bytes,8);if(bytes>200000000)throw std::runtime_error("Invalid phase stream length");
        std::vector<unsigned char> stream(bytes);read(stream.data(),stream.size());size_t cursor=0;
        auto varint=[&]() {uint32_t result=0;unsigned shift=0;while(true){if(cursor>=stream.size() || shift>=35)throw std::runtime_error("Invalid phase varint");unsigned b=stream[cursor++];result|=(b&127)<<shift;if(!(b&128))return result;shift+=7;}};
        g.values.resize(g.patterns*g.px*12);uint32_t zeros=0;
        for(size_t n=0;n<g.values.size();++n) {
            int delta=0;
            if(zeros)--zeros;
            else {uint32_t code=varint();if(code==0){uint32_t run=varint();if(!run || run>g.values.size()-n)throw std::runtime_error("Invalid phase zero run");zeros=run-1;}else{--code;delta=(code&1)?-int((code+1)/2):int(code/2);}}
            int x=int((n%120)/12),y=int(n%12),prediction=0;if(x)prediction+=g.values[n-12];if(y)prediction+=g.values[n-1];if(x && y)prediction-=g.values[n-13];
            int value=prediction+delta;if(value<0 || value>65535)throw std::runtime_error("Invalid decoded phase value");g.values[n]=uint16_t(value);
        }
        if(zeros || cursor!=stream.size())throw std::runtime_error("Trailing phase data");
        for(const auto& b:archdata::BLOCKS)if(b.vcross || (b.hcross && (b.left!=76 || b.right!=89 || b.hdelay<292)))throw std::runtime_error("Phase proof requires official crossing geometry");
        for(const auto& line:archdata::LINES) {if(line.vertical){for(int x=line.site+1;x<archdata::WIDTH;++x)if(x>=0)xgap[x]+=line.delay;}else{for(int y=line.site+1;y<archdata::HEIGHT;++y)if(y>=0)ygap[y]+=line.delay;}}
    }
    uint64_t gaps(archdata::XY a,archdata::XY b)const{return uint64_t(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x])))+uint64_t(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));}
    uint64_t lower(archdata::XY a,int port,archdata::XY b,int target)const {
        int pi=input_index[port];if(pi<0)throw std::runtime_error("Phase lower bound expects compact input");
        const auto& g=groups[1];auto mod=[](int v,int p){return (v%p+p)%p;};
        int dx=b.x-a.x,dy=b.y-a.y;
        unsigned phase=unsigned(mod(a.x-b.x,int(g.px))*12+mod(a.y-b.y,12));int64_t h=0;
        for(size_t k=0;k<4;++k) {
            size_t row=(k*archdata::P+target)*160+pi;
            int64_t residual=int64_t(g.base[row])+g.values[g.ids[row]*g.px*12+phase];
            int64_t value=int64_t(potential_lower_model::ax[k])*dx+int64_t(potential_lower_model::ay[k])*dy+residual;
            h=std::max(h,(value+11)/12);
        }
        return uint64_t(h)+gaps(a,b);
    }
};
