#pragma once
#include "local_path_oracle.hpp"
#include "cycle_prefix_bank.hpp"
#include <array>
#include <cstdint>
#include <limits>
#include <vector>

// Every returned bound is a concatenation of official arcs/nets and a tail witness.
class CyclePathOracle {
    struct Prefix {int long_index,dx1,dy1,dx2,dy2;uint32_t cost;uint32_t packed=16383;bool witness=false;};
    struct Long {int input,output,dx,dy;uint32_t net_cost,cycle;};
    LocalPathOracle tail;
    bool nominal=false;
    std::vector<Long> longs;
    std::array<std::vector<Prefix>,archdata::P> prefixes;
    std::vector<int> grid;
    std::vector<std::vector<int>> turn;
    static constexpr uint64_t absent=std::numeric_limits<uint64_t>::max();
    static constexpr uint32_t noarc=10000000;
    uint64_t segment(int x,int y,int tx,int ty) const {
        if(x<0 || y<0 || tx<0 || ty<0 || x>=archdata::WIDTH || tx>=archdata::WIDTH || y>=archdata::HEIGHT || ty>=archdata::HEIGHT) return absent;
        int left=std::min(x,tx),right=std::max(x,tx),lower=std::min(y,ty),upper=std::max(y,ty);
        if(!nominal) for(const auto& b:archdata::BLOCKS) if(left<=b.right && right>=b.left && lower<=b.upper && upper>=b.lower) return absent;
        uint64_t cost=0;
        for(const auto& line:archdata::LINES) {
            int a=line.vertical?left:lower,b=line.vertical?right:upper;
            if(a<=line.site && line.site<b) cost+=line.delay;
        }
        return cost;
    }
    uint64_t finish(int x,int y,int port,uint32_t target,uint64_t prefix,uint64_t best) const {
        if(prefix>=best || x<0 || y<0 || x>=archdata::WIDTH || y>=archdata::HEIGHT) return best;
        if(nominal) {
            auto t=archdata::SITES[target/archdata::P];
            auto value=tail.nominal_cost(port,target%archdata::P,t.x-x,t.y-y);
            return value==absent?best:std::min(best,prefix+value);
        }
        int site=grid[x*archdata::HEIGHT+y];
        if(site<0) return best;
        auto bound=tail.upper_bound(uint32_t(site)*archdata::P+port,target);
        return bound==absent?best:std::min(best,prefix+bound);
    }
public:
    explicit CyclePathOracle(const std::string& path,bool nominal_feature=false):tail(path),nominal(nominal_feature),grid(archdata::WIDTH*archdata::HEIGHT,-1) {
        std::array<std::vector<archdata::Arc>,archdata::P> outgoing;
        std::array<int,archdata::P> net_index;net_index.fill(-1);
        std::array<int,archdata::P> long_input;long_input.fill(-1);
        for(size_t i=0;i<std::size(archdata::SITES);++i) {auto xy=archdata::SITES[i];grid[xy.x*archdata::HEIGHT+xy.y]=i;}
        for(const auto& arc:archdata::ARCS) outgoing[arc.from].push_back(arc);
        for(size_t i=0;i<std::size(archdata::NETS);++i) {
            const auto& net=archdata::NETS[i];net_index[net.from]=i;auto v=archdata::VECTORS[net.vector];
            if(std::abs(v.x)+std::abs(v.y)<10) continue;
            uint32_t cycle=noarc;
            for(const auto& arc:outgoing[net.to]) if(arc.to==net.from) cycle=std::min(cycle,uint32_t(arc.delay+net.delay));
            if(cycle==noarc) continue;
            long_input[net.to]=longs.size();longs.push_back({net.to,net.from,v.x,v.y,uint32_t(net.delay),cycle});
        }
        turn.assign(longs.size(),std::vector<int>(longs.size(),noarc));
        for(size_t i=0;i<longs.size();++i) for(size_t j=0;j<longs.size();++j) {
            if(bool(longs[i].dx)==bool(longs[j].dx)) continue;
            for(const auto& arc:outgoing[longs[i].input]) if(arc.to==longs[j].output) turn[i][j]=std::min(turn[i][j],arc.delay+int(longs[j].net_cost));
        }
        for(const auto& entry:cycle_prefix_bank::entries) {
            int li=long_input[entry.target];
            if(li>=0) prefixes[entry.source].push_back({li,entry.dx,entry.dy,0,0,entry.packed&16383,entry.packed,true});
        }
        for(int source=0;source<archdata::P;++source) {
            int start=source,dx1=0,dy1=0;uint32_t firstcost=0;
            if(net_index[source]>=0) {
                const auto& net=archdata::NETS[net_index[source]];auto v=archdata::VECTORS[net.vector];
                start=net.to;dx1=v.x;dy1=v.y;firstcost=net.delay;
            }
            if(long_input[start]>=0) prefixes[source].push_back({long_input[start],dx1,dy1,0,0,firstcost});
            for(const auto& arc:outgoing[start]) if(net_index[arc.to]>=0) {
                const auto& net=archdata::NETS[net_index[arc.to]];
                if(long_input[net.to]<0) continue;
                auto v=archdata::VECTORS[net.vector];
                prefixes[source].push_back({long_input[net.to],dx1,dy1,v.x,v.y,firstcost+uint32_t(arc.delay+net.delay)});
            }
        }
    }
    uint64_t cap(uint32_t source,uint32_t target,uint64_t prediction) const {
        auto a=archdata::SITES[source/archdata::P],b=archdata::SITES[target/archdata::P];uint64_t best=prediction;
        for(const auto& p:prefixes[source%archdata::P]) {
            int mx=a.x+p.dx1,my=a.y+p.dy1,ex=mx+p.dx2,ey=my+p.dy2;
            uint64_t initial;
            if(p.witness) {
                initial=nominal?p.cost:LocalPathOracle::translated_bound(a,{ex,ey},p.packed);
                if(initial==absent) continue;
            } else {
                auto gap1=segment(a.x,a.y,mx,my),gap2=segment(mx,my,ex,ey);
                if(gap1==absent || gap2==absent) continue;
                initial=p.cost+gap1+gap2;
            }
            if(initial>=best) continue;
            const auto& first=longs[p.long_index];
            int remaining=first.dx?(b.x-ex)*(first.dx>0?1:-1):(b.y-ey)*(first.dy>0?1:-1);
            int span=std::abs(first.dx)+std::abs(first.dy);
            if(remaining < -12) continue;
            int hops=remaining>=0?remaining/span:0;
            for(int q=hops;q<=hops+1;++q) {
                int cx=ex+q*first.dx,cy=ey+q*first.dy;auto gap=segment(ex,ey,cx,cy);
                if(gap==absent) continue;
                uint64_t prefix=initial+uint64_t(q)*first.cycle+gap;
                best=finish(cx,cy,first.input,target,prefix,best);
                if(prefix>=best) continue;
                for(size_t j=0;j<longs.size();++j) {
                    if(turn[p.long_index][j]==int(noarc)) continue;
                    const auto& second=longs[j];
                    int rem=second.dx?(b.x-cx)*(second.dx>0?1:-1):(b.y-cy)*(second.dy>0?1:-1);
                    int length=std::abs(second.dx)+std::abs(second.dy);
                    if(rem < -12) continue;
                    int count=rem>=0?rem/length:0;
                    for(int n=std::max(1,count);n<=count+1;++n) {
                        int fx=cx+n*second.dx,fy=cy+n*second.dy;
                        if(std::abs(fx-b.x)>12 || std::abs(fy-b.y)>12) continue;
                        uint64_t head=prefix+turn[p.long_index][j]+uint64_t(n-1)*second.cycle;
                        if(head>=best) continue;
                        auto cost=segment(cx,cy,fx,fy);
                        if(cost!=absent) best=finish(fx,fy,second.input,target,head+cost,best);
                    }
                }
            }
        }
        return best;
    }
};
