#pragma once
#include "local_path_oracle.hpp"
#include "cycle_prefix_bank.hpp"
#include "potential_lower_model.hpp"
#include "routing_search.hpp"
#include <array>
#include <queue>
#include <vector>

// Search only certified paths, using long-wire inputs as transit vertices.
class MacroPathOracle {
    struct Edge {int target,dx,dy;uint32_t packed;};
    struct Item {uint64_t f,g;uint32_t node;bool operator<(const Item& x) const {return f>x.f;}};
    LocalPathOracle tail;
    Graph repeat_graph;
    const PhaseLowerBound* phase=nullptr;
    bool repeat_jumps=false;
    bool local_bridges=false;
    double priority_weight=1;
    struct Repeat{int net,dx,dy;uint32_t arc_cost;};
    std::vector<std::vector<Repeat>> repeats;
    std::vector<int> ports,grid;
    std::vector<uint64_t> xgap,ygap;
    bool include_gaps=false;
    std::array<int,archdata::P> index;
    std::array<std::vector<Edge>,archdata::P> entries;
    std::vector<std::vector<Edge>> edges;
    std::vector<uint64_t> distance;
    std::vector<uint32_t> stamp;
    uint32_t epoch=0;
    static constexpr uint64_t absent=UINT64_MAX;
    uint64_t heuristic(int x,int y,int port,archdata::XY target,int tp) const {
        auto phi=[](int a){return a-std::clamp(a-76,0,14);};
        int dx=phi(target.x)-phi(x),dy=target.y-y;int64_t best=0;
        for(size_t k=0;k<4;++k) {
            auto value=int64_t(potential_lower_model::ax[k])*dx+int64_t(potential_lower_model::ay[k])*dy+
              potential_lower_model::distance[k*archdata::P*archdata::P+port*archdata::P+tp];
            best=std::max(best,(value+11)/12);
        }
        auto result=uint64_t(best)+(include_gaps?uint64_t(std::llabs(int64_t(xgap[target.x])-int64_t(xgap[x])))+uint64_t(std::llabs(int64_t(ygap[target.y])-int64_t(ygap[y]))):0);
        return phase?std::max(result,phase->lower({x,y},port,target,tp)):result;
    }
public:
    uint64_t total_expanded=0,total_finished=0;
    explicit MacroPathOracle(const std::string& path,bool gap_heuristic=false,bool jumps=false,const PhaseLowerBound* bound=nullptr,bool bridges=false,double weight=1):tail(path),phase(bound),repeat_jumps(jumps),local_bridges(bridges),priority_weight(weight),grid(archdata::WIDTH*archdata::HEIGHT,-1) {
        if(!std::isfinite(weight) || weight<1 || weight>2)throw std::runtime_error("Invalid macro priority weight");
        include_gaps=gap_heuristic;xgap.resize(archdata::WIDTH);ygap.resize(archdata::HEIGHT);
        for(const auto& line:archdata::LINES) {auto& prefix=line.vertical?xgap:ygap;for(size_t coordinate=0;coordinate<prefix.size();++coordinate)if(int(coordinate)>line.site)prefix[coordinate]+=line.delay;}
        index.fill(-1);
        for(const auto& net:archdata::NETS) {
            auto v=archdata::VECTORS[net.vector];
            if(std::abs(v.x)+std::abs(v.y)>=10 && index[net.to]<0) {index[net.to]=ports.size();ports.push_back(net.to);}
        }
        for(size_t i=0;i<std::size(archdata::SITES);++i) {auto p=archdata::SITES[i];grid[p.x*archdata::HEIGHT+p.y]=int(i);}
        for(const auto& e:cycle_prefix_bank::entries) if(index[e.target]>=0)
            entries[e.source].push_back({index[e.target],e.dx,e.dy,e.packed});
        edges.resize(ports.size());
        repeats.resize(ports.size());
        for(size_t i=0;i<ports.size();++i) {
            for(size_t ni=0;ni<std::size(archdata::NETS);++ni){auto net=archdata::NETS[ni];if(net.to!=ports[i])continue;auto v=archdata::VECTORS[net.vector];for(auto arc:archdata::ARCS)if(arc.from==ports[i] && arc.to==net.from)repeats[i].push_back({int(ni),v.x,v.y,uint32_t(arc.delay)});}
            edges[i]=entries[ports[i]];
            for(const auto& arc:archdata::ARCS) if(arc.from==ports[i])
                for(const auto& net:archdata::NETS) if(net.from==arc.to && index[net.to]>=0) {
                    auto v=archdata::VECTORS[net.vector];auto cost=uint32_t(arc.delay+net.delay);
                    if(cost<16383) edges[i].push_back({index[net.to],v.x,v.y,cost|(1u<<30)|(1u<<31)});
                }
        }
        distance.resize(grid.size()*ports.size());stamp.resize(distance.size());
    }
    uint64_t cap(uint32_t source,uint32_t target,uint64_t upper,unsigned budget=256) {
        auto a=archdata::SITES[source/archdata::P],b=archdata::SITES[target/archdata::P];int tp=target%archdata::P;
        if(++epoch==0) {std::fill(stamp.begin(),stamp.end(),0);++epoch;}
        std::priority_queue<Item> heap;uint64_t best=upper;unsigned expanded=0;
        auto push=[&](int x,int y,int li,uint64_t g) {
            if(g>=best || x<0 || y<0 || x>=archdata::WIDTH || y>=archdata::HEIGHT) return;
            int coordinate=x*archdata::HEIGHT+y;if(grid[coordinate]<0)return;
            uint32_t node=coordinate*ports.size()+li;
            if(stamp[node]==epoch && distance[node]<=g)return;
            uint64_t h=heuristic(x,y,ports[li],b,tp);if(g+h>=best)return;uint64_t f=g+uint64_t(std::ceil(priority_weight*h));
            stamp[node]=epoch;distance[node]=g;heap.push({f,g,node});
        };
        if(index[source%archdata::P]>=0)push(a.x,a.y,index[source%archdata::P],0);
        for(const auto& edge:entries[source%archdata::P]) {
            archdata::XY t{a.x+edge.dx,a.y+edge.dy};auto cost=LocalPathOracle::translated_bound(a,t,edge.packed);
            if(cost!=absent)push(t.x,t.y,edge.target,cost);
        }
        while(!heap.empty() && expanded<budget) {
            auto current=heap.top();heap.pop();if(priority_weight==1 && current.f>=best)break;
            if(stamp[current.node]!=epoch || distance[current.node]!=current.g)continue;
            ++expanded;int li=current.node%ports.size(),coordinate=current.node/ports.size();
            int x=coordinate/archdata::HEIGHT,y=coordinate%archdata::HEIGHT;
            if(priority_weight!=1 && current.g+heuristic(x,y,ports[li],b,tp)>=best)continue;
            if(std::abs(x-b.x)<=12 && std::abs(y-b.y)<=12) {
                auto cost=tail.upper_bound(uint32_t(grid[coordinate])*archdata::P+ports[li],target);
                if(cost!=absent && current.g+cost<best) {best=current.g+cost;++total_finished;}
            }
            if(repeat_jumps)for(auto repeat:repeats[li]){
                auto phi=[](int a){return a-std::clamp(a-76,0,14);};
                int remaining=repeat.dx?(phi(b.x)-phi(x))*(repeat.dx>0?1:-1):(b.y-y)*(repeat.dy>0?1:-1);
                if(remaining<=0)continue;
                int hops=remaining/(std::abs(repeat.dx)+std::abs(repeat.dy));
                Node cursor=uint32_t(grid[coordinate]);uint64_t cost=current.g;
                for(int q=1;q<=hops+2;++q){auto move=repeat_graph.net_move(cursor,repeat.net,false);if(move.site==NONE)break;cost+=repeat.arc_cost+archdata::NETS[repeat.net].delay+move.delay;cursor=move.site;if(cost>=best)break;
                    if(q>=std::max(1,hops-2)){auto pos=archdata::SITES[cursor];push(pos.x,pos.y,li,cost);}
                }
            }
            if(local_bridges){
                int rx=(b.x-x)%10,ry=(b.y-y)%12;
                const int xs[]={0,rx,rx+(rx>=0?-10:10)},ys[]={0,ry,ry+(ry>=0?-12:12)};
                for(int xi=0;xi<3;++xi)for(int yi=0;yi<3;++yi){
                    if((xi>0 && xs[xi]==xs[0]) || (xi>1 && xs[xi]==xs[1]) || (yi>0 && ys[yi]==ys[0]) || (yi>1 && ys[yi]==ys[1]))continue;
                    int nx=x+xs[xi],ny=y+ys[yi];if(nx<0 || ny<0 || nx>=archdata::WIDTH || ny>=archdata::HEIGHT)continue;
                    int ns=grid[nx*archdata::HEIGHT+ny];if(ns<0)continue;
                    for(size_t j=0;j<ports.size();++j){if(j==size_t(li) && xs[xi]==0 && ys[yi]==0)continue;
                        if(current.g+heuristic(nx,ny,ports[j],b,tp)>=best)continue;
                        auto cost=tail.upper_bound(uint32_t(grid[coordinate])*archdata::P+ports[li],uint32_t(ns)*archdata::P+ports[j]);
                        if(cost!=absent)push(nx,ny,j,current.g+cost);
                    }
                }
            }
            for(const auto& edge:edges[li]) {
                archdata::XY start{x,y},end{x+edge.dx,y+edge.dy};
                auto cost=LocalPathOracle::translated_bound(start,end,edge.packed);
                if(cost!=absent)push(end.x,end.y,edge.target,current.g+cost);
            }
        }
        total_expanded+=expanded;return best;
    }
};
