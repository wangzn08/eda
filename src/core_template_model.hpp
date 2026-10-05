#pragma once
#include "routing_search.hpp"
#include <zlib.h>
#include "xz_decode.hpp"
#include <cstring>
#include "vertical_transient_model.hpp"
#include <memory>
// Exact finite-template storage; periodic extension remains approximate.
class CoreTemplateModel {
    std::array<int,496>index;
    std::vector<uint16_t>values;
    std::array<std::vector<std::pair<unsigned,unsigned>>,496>terminal;
    std::array<Distance,120>xgap{};
    std::array<Distance,550>ygap{};
    bool envelope;
    unsigned shell_x=0,shell_y=0,growth_cap=UINT_MAX;
    std::unique_ptr<VerticalTransientModel>vertical;
    Distance at(unsigned source,unsigned target,int x,int y)const{
        return values[((source*160+target)*59+x+29)*71+y+35];
    }
    Distance nominal(int port,int target,int dx,int dy)const{
        int ax=std::abs(dx),ay=std::abs(dy),qx=ax>29?(ax-20)/10:0,qy=ay>35?(ay-24)/12:0;
        if(qx)qx+=std::min(shell_x,unsigned((ax-qx*10)/10));
        if(qy)qy+=std::min(shell_y,unsigned((ay-qy*12)/12));
        int x=(dx<0?-1:1)*(ax-qx*10),y=(dy<0?-1:1)*(ay-qy*12);
        Distance best=INF;
        auto candidate=[&](int rx,int ry,int nx,int ny){
            Distance base=INF;
            for(auto end:terminal[target]){int64_t value=int64_t(at(index[port],end.first,rx,ry))+end.second;if(vertical)value+=vertical->correction(index[port],end.first,rx,dy,growth_cap);base=std::min(base,Distance(std::max<int64_t>(0,value)));}
            best=std::min(best,base+Distance(nx)*125+Distance(ny)*(dy>0?127:125));
        };
        if(!envelope){candidate(x,y,qx,qy);return best;}
        // Compare all representatives in the same period class, for long displacements.
        std::vector<std::pair<int,int>>xs,ys;
        if(ax<=29)xs.push_back({dx,0});
        else for(int rx=-29;rx<=29;++rx){int n=(dx<0?rx-dx:dx-rx);if(n>=0 && n%10==0)xs.push_back({rx,n/10});}
        if(ay<=35)ys.push_back({dy,0});
        else for(int ry=-35;ry<=35;++ry){int n=(dy<0?ry-dy:dy-ry);if(n>=0 && n%12==0)ys.push_back({ry,n/12});}
        for(auto a:xs)for(auto b:ys)candidate(a.first,b.first,a.second,b.second);
        return best;
    }
public:
    std::pair<float,float>gap_features(Node source,Node target)const{
        auto a=archdata::SITES[source/496],b=archdata::SITES[target/496];
        return {float(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x]))),float(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])))};
    }
    explicit CoreTemplateModel(const std::string&path,bool use_envelope=false,unsigned sx=0,unsigned sy=0,const std::string&transient_path="",unsigned cap=UINT_MAX):envelope(use_envelope),shell_x(sx),shell_y(sy),growth_cap(cap){
        if(sx>2 || sy>2 || (use_envelope && (sx || sy)))throw std::runtime_error("Invalid template shell policy");
        std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated core template");};
        char magic[8],hash[64];std::array<uint16_t,160>ports;uint64_t decoded;
        read(magic,8);read(hash,64);read(ports.data(),320);read(&decoded,8);
        if((std::string(magic,8)!="COREZL01" && std::string(magic,8)!="COREXZ01") || std::string(hash,64)!=archdata::HASH || decoded!=214476800)throw std::runtime_error("Invalid core template header");
        index.fill(-1);for(unsigned i=0;i<160;++i){if(ports[i]>=496 || index[ports[i]]>=0)throw std::runtime_error("Invalid core ports");index[ports[i]]=i;terminal[ports[i]].push_back({i,0});}
        if(!transient_path.empty()){if(sx || sy || use_envelope)throw std::runtime_error("Transient requires original anchor policy");vertical=std::make_unique<VerticalTransientModel>(transient_path,ports);}
        for(auto arc:archdata::ARCS)if(index[arc.from]>=0)terminal[arc.to].push_back({unsigned(index[arc.from]),unsigned(arc.delay)});
        std::vector<unsigned char>compressed((std::istreambuf_iterator<char>(f)),{});
        if(f.bad() || compressed.empty() || compressed.size()>100000000)throw std::runtime_error("Invalid core payload size");
        values.resize(decoded/2);if(std::string(magic,8)=="COREXZ01"){if(!decode_xz_exact(compressed.data(),compressed.size(),reinterpret_cast<unsigned char*>(values.data()),decoded))throw std::runtime_error("Invalid core XZ stream");}else{z_stream stream{};stream.next_in=compressed.data();stream.avail_in=unsigned(compressed.size());stream.next_out=reinterpret_cast<Bytef*>(values.data());stream.avail_out=unsigned(decoded);
        if(inflateInit(&stream)!=Z_OK)throw std::runtime_error("Core inflate initialization failed");
        int result=inflate(&stream,Z_FINISH);bool valid=result==Z_STREAM_END && stream.total_out==decoded && stream.avail_in==0;inflateEnd(&stream);
        if(!valid)throw std::runtime_error("Invalid core compressed stream");}
        for(size_t pair=0;pair<160*160;++pair)for(int x=0;x<59;++x)for(int y=0;y<71;++y){size_t i=pair*4189+x*71+y;int16_t delta;std::memcpy(&delta,&values[i],2);int value=delta;if(x)value+=values[i-71];if(y)value+=values[i-1];if(x && y)value-=values[i-72];if(value<0 || value>65535)throw std::runtime_error("Core inverse transform overflow");values[i]=uint16_t(value);}
        for(auto l:archdata::LINES){if(l.vertical)for(int x=l.site+1;x<120;++x)xgap[x]+=l.delay;else for(int y=l.site+1;y<550;++y)ygap[y]+=l.delay;}
    }
    Distance predict(const Graph&graph,Node source,Node target)const{
        if(source==target)return 0;Node site=source/496;int port=source%496,tp=target%496;auto b=archdata::SITES[target/496];Distance best=INF;
        auto bound=[&](Node s,int p){auto a=archdata::SITES[s];int dx=b.x-a.x,dy=b.y-a.y;Distance value=nominal(p,tp,dx,dy);if(std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89)value=std::min(value,nominal(p,tp,dx+(dx>0?-14:14),dy)+292);return value+Distance(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x])))+Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));};
        if(site==target/496)for(auto e:graph.local_out(port))if(e.port==tp)best=std::min(best,Distance(e.delay));
        auto after_net=[&](int ni,Distance cost){auto m=graph.net_move(site,ni,false);if(m.site!=NONE)best=std::min(best,cost+m.delay+archdata::NETS[ni].delay+bound(m.site,archdata::NETS[ni].to));};
        if(index[port]>=0)best=std::min(best,bound(site,port));else if(graph.net_out(port)>=0)after_net(graph.net_out(port),0);else for(auto e:graph.local_out(port))if(graph.net_out(e.port)>=0)after_net(graph.net_out(e.port),e.delay);
        return best;
    }
};
