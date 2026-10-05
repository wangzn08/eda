#pragma once
#include "phase_lower_bound.hpp"
// Research product graph: suffix must contain at least one vertical long wire.
// Paths without such a wire are bounded separately, then take the minimum.
class PhaseRequiredBound {
    std::array<int,archdata::P> index;
    std::vector<int16_t> values;
public:
    explicit PhaseRequiredBound(const std::string& path) {
        std::ifstream f(path,std::ios::binary);char magic[8];uint32_t header[7];std::array<uint16_t,160> ports;
        f.read(magic,8);f.read(reinterpret_cast<char*>(header),sizeof(header));f.read(reinterpret_cast<char*>(ports.data()),320);
        if(std::string(magic,8)!="PHASYREQ" || header[1]!=496 || header[2]!=160 || header[3]!=4 || header[4]!=10 || header[5]!=10 || header[6]!=12)throw std::runtime_error("Invalid required phase asset");
        index.fill(-1);for(int i=0;i<160;++i){if(ports[i]>=496 || index[ports[i]]>=0 || ports[i]!=archdata::NETS[i].to)throw std::runtime_error("Invalid required phase ports");index[ports[i]]=i;}values.resize(4*496*160*120);f.read(reinterpret_cast<char*>(values.data()),values.size()*2);if(!f)throw std::runtime_error("Truncated required phase asset");
    }
    uint64_t lower(archdata::XY a,int port,archdata::XY b,int target,const PhaseLowerBound& base)const {
        int pi=index[port];if(pi<0)throw std::runtime_error("Invalid required phase port");
        int dx=b.x-a.x,dy=b.y-a.y;auto mod=[](int v,int p){return (v%p+p)%p;};int phase=mod(-dx,10)*12+mod(-dy,12);int64_t h=0;
        for(int k=0;k<4;++k){int64_t v=int64_t(potential_lower_model::ax[k])*dx+int64_t(potential_lower_model::ay[k])*dy+values[((k*496+target)*160+pi)*120+phase];h=std::max(h,(v+11)/12);}
        // Every short vertical Arc+Net costs at least 21 ps per cell.
        // Horizontal moves cannot reduce this bound; extra gap costs are separate.
        uint64_t conditioned=uint64_t(std::min(h,int64_t(21)*std::abs(dy)))+base.gaps(a,b);
        return std::max(conditioned,base.lower(a,port,b,target));
    }
};
