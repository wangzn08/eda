#pragma once
#include "routing_search.hpp"
#include <zlib.h>
#include "xz_decode.hpp"
#include <cstring>
#include "vertical_transient_model.hpp"
#include "horizontal_transient_model.hpp"
#include <memory>
// Exact finite-template storage; periodic extension remains approximate.
class CoreTemplateModel {
    std::array<int,496>index;
    std::vector<uint16_t>values;
    std::array<std::vector<std::pair<unsigned,unsigned>>,496>terminal;
    std::array<Distance,120>xgap{};
    std::array<Distance,550>ygap{};
    bool envelope,has_far=false,corridor_geometry=false;
    unsigned shell_x=0,shell_y=0,growth_cap=UINT_MAX,far_period=4;
    std::unique_ptr<VerticalTransientModel>vertical;
    std::unique_ptr<HorizontalTransientModel>horizontal;
    struct JointCell {int32_t base[4];int32_t slope_x,slope_y;};
    std::vector<JointCell>joint;
    struct FarJointCell {uint16_t base[4];int16_t horizontal_delta;uint16_t slope_x,slope_near_y,slope_far_y;};
    static_assert(sizeof(FarJointCell)==16,"Compact piecewise cell size");
    std::vector<FarJointCell>far_joint;
    struct ShortVerticalCell {uint16_t base[4],slope;};
    static_assert(sizeof(ShortVerticalCell)==10,"Short vertical cell size");
    std::vector<ShortVerticalCell>short_vertical;
    std::vector<int>corridor_ports;
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
            for(auto end:terminal[target]){int64_t value;
                if(!short_vertical.empty() && nx==0 && ny>0){
                    unsigned iy=(ry>0?12:0)+std::abs(ry)-24;
                    const auto& cell=short_vertical[((size_t(index[port])*160+end.first)*59+rx+29)*24+iy];
                    if(ny==1)value=cell.base[0];else if(ny==2)value=cell.base[1];
                    else if(unsigned(ny)<far_period)value=int(cell.base[1])+(int(cell.base[2])-int(cell.base[1]))*(ny-2)/int(far_period-2);
                    else if(unsigned(ny)==far_period)value=cell.base[2];else value=cell.base[3]+(int64_t(ny)-far_period-1)*cell.slope;
                    value+=end.second;
                }else if((!joint.empty() || !far_joint.empty()) && nx>0 && ny>0){
                    unsigned ix=(rx>0?10:0)+std::abs(rx)-20,iy=(ry>0?12:0)+std::abs(ry)-24;
                    size_t ji=(size_t(index[port])*160+end.first)*480+ix*24+iy;
                    if(!far_joint.empty()){
                        const auto& cell=far_joint[ji];int64_t v;
                        if(ny==1)v=cell.base[0];
                        else if(ny==2)v=cell.base[1];
                        else if(unsigned(ny)<far_period)v=int(cell.base[1])+(int(cell.base[2])-int(cell.base[1]))*(ny-2)/int(far_period-2);
                        else if(unsigned(ny)==far_period)v=cell.base[2];
                        else v=cell.base[3]+(int64_t(ny)-far_period-1)*cell.slope_far_y;
                        if(nx>=2)v+=cell.horizontal_delta+int64_t(nx-2)*cell.slope_x;
                        value=v+end.second;
                    }else{
                        const auto& cell=joint[ji];
                        value=cell.base[(nx>=2?2:0)+(ny>=2?1:0)]+int64_t(std::min(unsigned(std::max(0,nx-2)),growth_cap))*cell.slope_x+int64_t(std::min(unsigned(std::max(0,ny-2)),growth_cap))*cell.slope_y+end.second;
                    }
                }else{value=int64_t(at(index[port],end.first,rx,ry))+end.second;if(vertical)value+=vertical->correction(index[port],end.first,rx,dy,growth_cap);if(horizontal)value+=horizontal->correction(index[port],end.first,ry,dx,growth_cap);}base=std::min(base,Distance(std::max<int64_t>(0,value)));}
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
    void enable_corridor_hubs(unsigned count){
        if(!corridor_geometry || !count || count>32)throw std::runtime_error("Corridor hubs require geometry and1..32 hubs");
        std::vector<std::pair<unsigned,int>>ports;
        for(auto net:archdata::NETS){auto v=archdata::VECTORS[net.vector];if(std::abs(v.x)+std::abs(v.y)>=10)ports.push_back({net.delay,net.to});}
        std::sort(ports.begin(),ports.end());for(auto p:ports)if(std::find(corridor_ports.begin(),corridor_ports.end(),p.second)==corridor_ports.end()){corridor_ports.push_back(p.second);if(corridor_ports.size()==count)break;}
    }
    void enable_short_vertical_layout(){
        if(!has_far || far_joint.empty())throw std::runtime_error("Wide joint layout requires far joint layout");
        short_vertical.resize(size_t(160)*160*59*24);
        for(unsigned s=0;s<160;++s)for(unsigned t=0;t<160;++t)for(int x=-29;x<=29;++x)for(unsigned iy=0;iy<24;++iy){
            int sy=iy<12?-1:1,r=iy%12,y=sy*(24+r);auto& cell=short_vertical[((size_t(s)*160+t)*59+x+29)*24+iy];
            unsigned bands[4]={36,48,24+12*far_period,36+12*far_period};int v[4];
            for(unsigned b=0;b<4;++b){v[b]=vertical->correction(s,t,x,sy*(bands[b]+r),growth_cap);int base=int(at(s,t,x,y))+v[b];if(base<0 || base>65535)throw std::runtime_error("Short joint base overflow");cell.base[b]=uint16_t(base);}
            int slope=std::max(0,v[3]-v[2]);if(slope>65535)throw std::runtime_error("Short joint slope overflow");cell.slope=uint16_t(slope);
        }
    }
    void enable_joint_layout(){
        if(!vertical || !horizontal || envelope || shell_x || shell_y)throw std::runtime_error("Joint layout requires both original-anchor transients");
        if(has_far)far_joint.resize(size_t(160)*160*480);else joint.resize(size_t(160)*160*480);
        for(unsigned source=0;source<160;++source)for(unsigned target=0;target<160;++target)for(unsigned ix=0;ix<20;++ix)for(unsigned iy=0;iy<24;++iy){
            int sx=ix<10?-1:1,sy=iy<12?-1:1,x=sx*(20+ix%10),y=sy*(24+iy%12);
            int32_t h[2]={horizontal->correction(source,target,y,sx*(30+ix%10),growth_cap),horizontal->correction(source,target,y,sx*(40+ix%10),growth_cap)};
            int32_t v[2]={vertical->correction(source,target,x,sy*(36+iy%12),growth_cap),vertical->correction(source,target,x,sy*(48+iy%12),growth_cap)};
            size_t ji=(size_t(source)*160+target)*480+ix*24+iy;
            if(has_far){
                auto& fc=far_joint[ji];
                int32_t vf[2]={vertical->correction(source,target,x,sy*(24+12*int(far_period)+int(iy%12)),growth_cap),vertical->correction(source,target,x,sy*(36+12*int(far_period)+int(iy%12)),growth_cap)};
                int32_t bases[4]={int32_t(at(source,target,x,y))+h[0]+v[0],int32_t(at(source,target,x,y))+h[0]+v[1],int32_t(at(source,target,x,y))+h[0]+vf[0],int32_t(at(source,target,x,y))+h[0]+vf[1]};
                for(unsigned b=0;b<4;++b){if(bases[b]<0 || bases[b]>65535)throw std::runtime_error("Compact joint base overflow");fc.base[b]=uint16_t(bases[b]);}
                int delta=h[1]-h[0];if(delta < -32768 || delta>32767)throw std::runtime_error("Compact joint delta overflow");fc.horizontal_delta=int16_t(delta);
                auto slope=[](int d){if(d>65535)throw std::runtime_error("Compact joint slope overflow");return uint16_t(std::max(0,d));};
                fc.slope_x=slope(delta);fc.slope_near_y=slope(v[1]-v[0]);fc.slope_far_y=slope(vf[1]-vf[0]);
            }else{
                auto& cell=joint[ji];
                for(unsigned a=0;a<2;++a)for(unsigned b=0;b<2;++b)cell.base[a*2+b]=int32_t(at(source,target,x,y))+h[a]+v[b];
                cell.slope_x=std::max(0,h[1]-h[0]);cell.slope_y=std::max(0,v[1]-v[0]);
            }
        }
    }
    std::pair<float,float>gap_features(Node source,Node target)const{
        auto a=archdata::SITES[source/496],b=archdata::SITES[target/496];
        return {float(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x]))),float(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])))};
    }
    explicit CoreTemplateModel(const std::string&path,bool use_envelope=false,unsigned sx=0,unsigned sy=0,const std::string&transient_path="",unsigned cap=UINT_MAX,const std::string&horizontal_path="",const std::string&far_path="",bool use_corridor=false):envelope(use_envelope),corridor_geometry(use_corridor),shell_x(sx),shell_y(sy),growth_cap(cap){
        if(sx>2 || sy>2 || (use_envelope && (sx || sy)))throw std::runtime_error("Invalid template shell policy");
        std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated core template");};
        char magic[8],hash[64];std::array<uint16_t,160>ports;uint64_t decoded;
        read(magic,8);read(hash,64);read(ports.data(),320);read(&decoded,8);
        if((std::string(magic,8)!="COREZL01" && std::string(magic,8)!="COREXZ01") || std::string(hash,64)!=archdata::HASH || decoded!=214476800)throw std::runtime_error("Invalid core template header");
        index.fill(-1);for(unsigned i=0;i<160;++i){if(ports[i]>=496 || index[ports[i]]>=0)throw std::runtime_error("Invalid core ports");index[ports[i]]=i;terminal[ports[i]].push_back({i,0});}
        if(!transient_path.empty()){if(sx || sy || use_envelope)throw std::runtime_error("Transient requires original anchor policy");vertical=std::make_unique<VerticalTransientModel>(transient_path,ports);}
        if(!horizontal_path.empty()){if(sx || sy || use_envelope)throw std::runtime_error("Horizontal transient requires original anchors");horizontal=std::make_unique<HorizontalTransientModel>(horizontal_path,ports);}
        if(!far_path.empty()){if(!vertical || cap!=UINT_MAX)throw std::runtime_error("Far delta requires vertical transient and unlimited growth cap");vertical->load_far_delta(far_path,ports);far_period=vertical->first_far_period();has_far=true;}
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
        auto bound=[&](Node s,int p){auto a=archdata::SITES[s];int dx=b.x-a.x,dy=b.y-a.y;Distance value=nominal(p,tp,dx,dy);if(std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89){
                if(corridor_geometry)for(const auto& block:archdata::BLOCKS)if(block.left==76 && block.right==89 && a.y>=block.lower && a.y<=block.upper && b.y>=block.lower && b.y<=block.upper){
                    value=INF;
                    auto corridor=[&](int cy,bool lower){
                        if(corridor_ports.empty()){int extra=lower?std::min(a.y,b.y)-block.lower+1:block.upper-std::max(a.y,b.y)+1;return nominal(p,tp,dx,(lower?-1:1)*(std::abs(dy)+2*extra));}
                        Distance best=INF;int cx=82;
                        for(int hub:corridor_ports){Distance first=nominal(p,hub,cx-a.x,cy-a.y),second=nominal(hub,tp,b.x-cx,b.y-cy);best=std::min(best,first+second);}
                        Distance detour=Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[cy])))+Distance(std::llabs(int64_t(ygap[b.y])-int64_t(ygap[cy])))-Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));
                        return best+detour;
                    };
                    if(block.lower>0)value=std::min(value,corridor(block.lower-1,true));
                    if(block.upper+1<archdata::HEIGHT)value=std::min(value,corridor(block.upper+1,false));
                    break;
                }
                value=std::min(value,nominal(p,tp,dx+(dx>0?-14:14),dy)+292);
            }return value+Distance(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x])))+Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));};
        if(site==target/496)for(auto e:graph.local_out(port))if(e.port==tp)best=std::min(best,Distance(e.delay));
        auto after_net=[&](int ni,Distance cost){auto m=graph.net_move(site,ni,false);if(m.site!=NONE)best=std::min(best,cost+m.delay+archdata::NETS[ni].delay+bound(m.site,archdata::NETS[ni].to));};
        if(index[port]>=0)best=std::min(best,bound(site,port));else if(graph.net_out(port)>=0)after_net(graph.net_out(port),0);else for(auto e:graph.local_out(port))if(graph.net_out(e.port)>=0)after_net(graph.net_out(e.port),e.delay);
        return best;
    }
};
