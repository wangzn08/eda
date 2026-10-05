#pragma once
#include "routing_search.hpp"
// Nominal finite-window paths extrapolated by minimum long-wire cycles.
// This is an approximation: no path or error certificate is claimed.
class PeriodicDenseModel {
    std::array<int,496> index;std::vector<uint16_t> values,conditioned;
    std::array<uint64_t,120>xgap{};std::array<uint64_t,550>ygap{};
    uint64_t nominal(int port,int target,int dx,int dy)const {
        int ax=std::abs(dx),ay=std::abs(dy),qx=ax>29?(ax-20)/10:0,qy=ay>35?(ay-24)/12:0;
        int x=(dx<0?-1:1)*(ax-qx*10),y=(dy<0?-1:1)*(ay-qy*12);
        uint64_t value=values[((index[port]*496+target)*59+x+29)*71+y+35];
        if(!conditioned.empty() && (qx || qy)) {
            int rx=std::abs(x)-20,ry=std::abs(y)-24,k=(dx<0?2:0)+(dy<0?1:0),column;
            if(qx && qy)column=2836+k*120+rx*12+ry;
            else if(qx)column=(dx<0?10:0)*71+rx*71+y+35;
            else column=1420+(dy<0?12:0)*59+ry*59+x+29;
            value=conditioned[(index[port]*496+target)*3316+column];
        }
        return value+uint64_t(qx)*125+uint64_t(qy)*(dy>0?127:125);
    }
public:
    explicit PeriodicDenseModel(const std::string&path){
        std::ifstream f(path,std::ios::binary);char magic[8],hash[64];std::array<uint16_t,160>ports;
        f.read(magic,8);f.read(hash,64);if(std::string(hash,64)!=archdata::HASH)throw std::runtime_error("Dense architecture mismatch");
        bool compressed=std::string(magic,8)=="DENSECP1";uint32_t groups=1;
        if(compressed){f.read(reinterpret_cast<char*>(&groups),4);if(groups<1 || groups>2)throw std::runtime_error("Invalid dense groups");}
        else if(std::string(magic,8)!="ANCHOR02")throw std::runtime_error("Dense asset format mismatch");
        f.read(reinterpret_cast<char*>(ports.data()),320);index.fill(-1);for(int i=0;i<160;++i){if(ports[i]>=496 || index[ports[i]]>=0)throw std::runtime_error("Invalid dense ports");index[ports[i]]=i;}
        values.resize(160*496*59*71);
        if(!compressed){f.read(reinterpret_cast<char*>(values.data()),values.size()*2);if(!f)throw std::runtime_error("Truncated dense asset");}
        else {
            auto varint=[&]{uint32_t v=0;for(unsigned shift=0;shift<35;shift+=7){int byte=f.get();if(byte<0)throw std::runtime_error("Truncated dense code");v|=uint32_t(byte&127)<<shift;if(!(byte&128))return v;}throw std::runtime_error("Invalid dense code");};
            for(uint32_t group=0;group<groups;++group){if(group)conditioned.resize(160*496*3316);auto&data=group?conditioned:values;
                std::vector<std::pair<int,int>>shapes=group?std::vector<std::pair<int,int>>{{20,71},{24,59},{10,12},{10,12},{10,12},{10,12}}:std::vector<std::pair<int,int>>{{59,71}};
                uint32_t zeros=0;size_t offset=0;
                for(int pair=0;pair<160*496;++pair)for(auto shape:shapes){int nx=shape.first,ny=shape.second;for(int n=0;n<nx*ny;++n){int delta=0;if(zeros)--zeros;else{auto code=varint();if(!code){auto run=varint();if(!run || run>data.size()-offset-size_t(n))throw std::runtime_error("Invalid dense run");zeros=run-1;}else{--code;delta=(code&1)?-int((code+1)/2):int(code/2);}}
                    int x=n/ny,y=n%ny,pred=0;size_t i=offset+n;if(x)pred+=data[i-ny];if(y)pred+=data[i-1];if(x && y)pred-=data[i-ny-1];int v=pred+delta;if(v<0 || v>65535)throw std::runtime_error("Dense decoding overflow");data[i]=uint16_t(v);}
                    offset+=nx*ny;
                }
                if(zeros || offset!=data.size())throw std::runtime_error("Invalid dense group length");
            }
            if(f.get()!=std::char_traits<char>::eof())throw std::runtime_error("Trailing dense data");
        }
        for(auto l:archdata::LINES){if(l.vertical)for(int x=l.site+1;x<120;++x)xgap[x]+=l.delay;else for(int y=l.site+1;y<550;++y)ygap[y]+=l.delay;}
    }
    void load_conditioned(const std::string&path){std::ifstream f(path,std::ios::binary);char magic[8],hash[64];std::array<uint16_t,160>ports;f.read(magic,8);f.read(hash,64);f.read(reinterpret_cast<char*>(ports.data()),320);if(std::string(magic,8)!="ANCHOR03" || std::string(hash,64)!=archdata::HASH)throw std::runtime_error("Conditioned asset mismatch");for(int i=0;i<160;++i)if(index[ports[i]]!=i)throw std::runtime_error("Conditioned port mismatch");conditioned.resize(160*496*3316);f.read(reinterpret_cast<char*>(conditioned.data()),conditioned.size()*2);if(!f)throw std::runtime_error("Truncated conditioned asset");}
    uint64_t predict(const Graph&graph,Node source,Node target,bool skip=true)const {
        if(source==target)return 0;Node site=source/496;int port=source%496,tp=target%496;auto b=archdata::SITES[target/496];Distance best=INF;
        auto bound=[&](Node s,int p){auto a=archdata::SITES[s];int dx=b.x-a.x,dy=b.y-a.y;uint64_t value=nominal(p,tp,dx,dy);if(skip && std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89)value=std::min(value,nominal(p,tp,dx+(dx>0?-14:14),dy)+292);return value+uint64_t(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x])))+uint64_t(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));};
        if(site==target/496)for(auto e:graph.local_out(port))if(e.port==tp)best=std::min(best,Distance(e.delay));
        auto after_net=[&](int ni,Distance cost){auto m=graph.net_move(site,ni,false);if(m.site!=NONE)best=std::min(best,cost+m.delay+archdata::NETS[ni].delay+bound(m.site,archdata::NETS[ni].to));};
        if(index[port]>=0)best=std::min(best,bound(site,port));else if(graph.net_out(port)>=0)after_net(graph.net_out(port),0);else for(auto e:graph.local_out(port))if(graph.net_out(e.port)>=0)after_net(graph.net_out(e.port),e.delay);
        return best;
    }
};
