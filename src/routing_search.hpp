#pragma once
#include "architecture_data.hpp"
#include "phase_lower_bound.hpp"
#include "potential_lower_model.hpp"
#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

using Node = uint32_t;
using Distance = uint64_t;
constexpr Node NONE = std::numeric_limits<Node>::max();
constexpr Node SETTLED = NONE - 1;
constexpr Distance INF = std::numeric_limits<Distance>::max()/4;

struct Move { Node site=NONE; uint32_t delay=0; };
struct LocalEdge { uint16_t port; uint32_t delay; };

// Memoization contains predictions computed in this process, never answers.
class PredictionCache {
    struct Entry {uint64_t key=UINT64_MAX,value=0;};
    std::vector<Entry> entries;
    size_t used=0;
    static uint64_t hash(uint64_t x) {
        x^=x>>30;x*=0xbf58476d1ce4e5b9ULL;x^=x>>27;x*=0x94d049bb133111ebULL;return x^(x>>31);
    }
public:
    uint64_t hits=0,misses=0;
    PredictionCache():entries(1u<<21) {}
    bool get(uint64_t key,Distance& value) {
        size_t slot=hash(key)&(entries.size()-1);
        for(unsigned probe=0;probe<64;++probe,slot=(slot+1)&(entries.size()-1)) {
            if(entries[slot].key==key) {value=entries[slot].value;++hits;return true;}
            if(entries[slot].key==UINT64_MAX) break;
        }
        ++misses;return false;
    }
    void put(uint64_t key,Distance value) {
        if(used>=entries.size()*3/4) return;
        size_t slot=hash(key)&(entries.size()-1);
        for(unsigned probe=0;probe<64;++probe,slot=(slot+1)&(entries.size()-1)) {
            if(entries[slot].key==UINT64_MAX) {entries[slot]={key,value};++used;return;}
            if(entries[slot].key==key) return;
        }
    }
};

class FastPinParser {
    std::vector<int> grid;
    std::unordered_map<std::string_view,unsigned> ports;
public:
    FastPinParser():grid(archdata::WIDTH*archdata::HEIGHT,-1) {
        for(size_t i=0;i<std::size(archdata::SITES);++i) {
            const auto& p=archdata::SITES[i];
            grid[p.x*archdata::HEIGHT+p.y]=static_cast<int>(i);
        }
        ports.reserve(archdata::P);
        for(int i=0;i<archdata::P;++i) ports.emplace(archdata::PORTS[i],i);
    }
    Node pin(std::string_view text) const {
        if(text.substr(0,4)!="SRB_") throw std::runtime_error("Invalid pin: "+std::string(text));
        size_t under=text.find('_',4),slash=text.find('/',4);
        if(under==text.npos || slash==text.npos || under>=slash)
            throw std::runtime_error("Invalid pin: "+std::string(text));
        int x=-1,y=-1;
        auto px=std::from_chars(text.data()+4,text.data()+under,x);
        auto py=std::from_chars(text.data()+under+1,text.data()+slash,y);
        if(px.ec!=std::errc() || py.ec!=std::errc() || px.ptr!=text.data()+under || py.ptr!=text.data()+slash
           || x<0 || x>=archdata::WIDTH || y<0 || y>=archdata::HEIGHT)
            throw std::runtime_error("Invalid coordinates: "+std::string(text));
        int site=grid[x*archdata::HEIGHT+y];
        auto found=ports.find(text.substr(slash+1));
        if(site<0 || found==ports.end()) throw std::runtime_error("Unknown pin: "+std::string(text));
        return static_cast<Node>(site)*archdata::P+found->second;
    }
};

class Graph {
    std::vector<int> grid;
    std::vector<Move> forward, backward;
    std::array<std::vector<LocalEdge>, archdata::P> arcs, reverse_arcs;
    std::array<int, archdata::P> net_from, net_to;
    std::unordered_map<std::string, unsigned> port_ids;

    int site_at(int x, int y) const {
        if(x<0 || x>=archdata::WIDTH || y<0 || y>=archdata::HEIGHT) return -1;
        return grid[x*archdata::HEIGHT+y];
    }

    // V0.3: only crossable Blocks are skipped while counting wire span.
    Move move(int x, int y, int dx, int dy) const {
        const int ox=x, oy=y, sx=(dx>0)-(dx<0), sy=(dy>0)-(dy<0);
        int remaining=std::abs(dx)+std::abs(dy);
        uint32_t cost=0;
        uint64_t crossed=0;
        while(remaining) {
            x+=sx; y+=sy;
            if(x<0 || x>=archdata::WIDTH || y<0 || y>=archdata::HEIGHT) return {};
            bool skip=false;
            for(size_t i=0;i<std::size(archdata::BLOCKS);++i) {
                const auto& b=archdata::BLOCKS[i];
                if(x>=b.left && x<=b.right && y>=b.lower && y<=b.upper && (dx?b.hcross:b.vcross)) {
                    skip=true;
                    if(!(crossed&(uint64_t(1)<<i))) {
                        cost+=dx?b.hdelay:b.vdelay;
                        crossed|=uint64_t(1)<<i;
                    }
                    break;
                }
            }
            if(!skip) --remaining;
        }
        int destination=site_at(x,y);
        if(destination<0) return {};
        for(const auto& line:archdata::LINES) {
            const int u=line.vertical?ox:oy, v=line.vertical?x:y;
            if(std::min(u,v)<=line.site && line.site<std::max(u,v)) cost+=line.delay;
        }
        return {static_cast<Node>(destination),cost};
    }

public:
    Node nodes() const { return std::size(archdata::SITES)*archdata::P; }
    Node sites() const { return std::size(archdata::SITES); }
    Graph():grid(archdata::WIDTH*archdata::HEIGHT,-1),
            forward(std::size(archdata::SITES)*archdata::K), backward(forward.size()) {
        static_assert(std::size(archdata::BLOCKS)<=64);
        net_from.fill(-1); net_to.fill(-1);
        for(size_t i=0;i<std::size(archdata::SITES);++i) {
            const auto& p=archdata::SITES[i];
            grid[p.x*archdata::HEIGHT+p.y]=static_cast<int>(i);
        }
        for(int i=0;i<archdata::P;++i) port_ids.emplace(archdata::PORTS[i],i);
        for(const auto& a:archdata::ARCS) {
            if(a.delay<0) throw std::runtime_error("Negative arc weight");
            arcs[a.from].push_back({static_cast<uint16_t>(a.to),static_cast<uint32_t>(a.delay)});
            reverse_arcs[a.to].push_back({static_cast<uint16_t>(a.from),static_cast<uint32_t>(a.delay)});
        }
        for(size_t i=0;i<std::size(archdata::NETS);++i) {
            const auto& n=archdata::NETS[i];
            if(net_from[n.from]>=0 || net_to[n.to]>=0) throw std::runtime_error("Baseline requires unique Net per inter-port");
            net_from[n.from]=net_to[n.to]=static_cast<int>(i);
        }
        for(size_t i=0;i<std::size(archdata::SITES);++i) {
            const auto& p=archdata::SITES[i];
            for(int k=0;k<archdata::K;++k) {
                auto v=archdata::VECTORS[k];
                auto m=move(p.x,p.y,v.x,v.y);
                forward[i*archdata::K+k]=m;
                if(m.site!=NONE) {
                    auto& reverse=backward[m.site*archdata::K+k];
                    if(reverse.site!=NONE) throw std::runtime_error("Non-injective Net mapping; reverse adjacency needs extension");
                    reverse={static_cast<Node>(i),m.delay};
                }
            }
        }
    }

    Node pin(const std::string& s) const {
        if(s.compare(0,4,"SRB_")!=0) throw std::runtime_error("Invalid pin: "+s);
        auto under=s.find('_',4), slash=s.find('/',4);
        if(under==std::string::npos || slash==std::string::npos || under>=slash) throw std::runtime_error("Invalid pin: "+s);
        int x=-1,y=-1;
        auto px=std::from_chars(s.data()+4,s.data()+under,x);
        auto py=std::from_chars(s.data()+under+1,s.data()+slash,y);
        if(px.ec!=std::errc() || py.ec!=std::errc() || px.ptr!=s.data()+under || py.ptr!=s.data()+slash) throw std::runtime_error("Invalid coordinates: "+s);
        int site=site_at(x,y);
        auto it=port_ids.find(s.substr(slash+1));
        if(site<0 || it==port_ids.end()) throw std::runtime_error("Unknown pin: "+s);
        return static_cast<Node>(site)*archdata::P+it->second;
    }

    const std::vector<LocalEdge>& local_out(unsigned p) const { return arcs[p]; }
    const std::vector<LocalEdge>& local_in(unsigned p) const { return reverse_arcs[p]; }
    int net_out(unsigned p) const { return net_from[p]; }
    int net_in(unsigned p) const { return net_to[p]; }
    Move net_move(Node site,int net,bool reverse) const {
        return (reverse?backward:forward)[site*archdata::K+archdata::NETS[net].vector];
    }

    template<class Visitor> void neighbors(Node u,bool reverse,Visitor visit) const {
        Node site=u/archdata::P, p=u%archdata::P;
        const auto& local=reverse?reverse_arcs[p]:arcs[p];
        for(auto e:local) visit(site*archdata::P+e.port,e.delay);
        int ni=reverse?net_to[p]:net_from[p];
        if(ni>=0) {
            const auto& n=archdata::NETS[ni];
            auto m=(reverse?backward:forward)[site*archdata::K+n.vector];
            if(m.site!=NONE) visit(m.site*archdata::P+(reverse?n.from:n.to),m.delay+n.delay);
        }
    }
};

// Addressable binary heap: at most one live entry per node, avoiding stale-entry growth.
class Frontier {
    std::vector<Distance> distances;
    std::vector<Node> positions, heap, touched;
    bool less(Node a,Node b) const {
        return distances[a]<distances[b] || (distances[a]==distances[b] && a<b);
    }
    void swap_positions(size_t a,size_t b) {
        std::swap(heap[a],heap[b]); positions[heap[a]]=a; positions[heap[b]]=b;
    }
public:
    explicit Frontier(size_t n):distances(n),positions(n,NONE) {}
    void reset() { for(Node n:touched) positions[n]=NONE; touched.clear(); heap.clear(); }
    bool empty() const { return heap.empty(); }
    Distance top() const { return heap.empty()?INF:distances[heap[0]]; }
    Distance get(Node n) const { return positions[n]==NONE?INF:distances[n]; }
    // A* keeps its own queue; retain distances and touched-state reset here.
    bool record(Node n,Distance value) {
        if(value>=get(n))return false;
        if(positions[n]==NONE)touched.push_back(n);
        positions[n]=SETTLED;distances[n]=value;return true;
    }
    bool improve(Node n,Distance value) {
        if(positions[n]==SETTLED || value>=get(n)) return false;
        size_t at;
        if(positions[n]==NONE) {
            at=heap.size(); positions[n]=at; heap.push_back(n); touched.push_back(n);
        } else at=positions[n];
        distances[n]=value;
        while(at && less(heap[at],heap[(at-1)/2])) {
            size_t parent=(at-1)/2; swap_positions(at,parent); at=parent;
        }
        return true;
    }
    Node pop() {
        Node result=heap[0];
        swap_positions(0,heap.size()-1); heap.pop_back(); positions[result]=SETTLED;
        size_t at=0;
        while(at*2+1<heap.size()) {
            size_t child=at*2+1;
            if(child+1<heap.size() && less(heap[child+1],heap[child])) ++child;
            if(!less(heap[child],heap[at])) break;
            swap_positions(child,at); at=child;
        }
        return result;
    }
};

struct SearchStats {uint64_t settled=0, relaxations=0;Distance lower=INF,upper=INF;};

class CompactSolver {
    const Graph& graph;
    std::array<int,archdata::P> input_index;
    std::vector<uint16_t> input_ports;
    Frontier forward,backward;
    std::vector<Node> trace_parent;
    std::vector<int32_t> balanced_potentials;std::vector<uint32_t> balanced_stamps;uint32_t balanced_epoch=0;
    std::vector<Distance> phase_cached_lower;std::vector<uint32_t> phase_cached_stamp;uint32_t phase_cached_epoch=0;
    Node state(Node site,int port) const { return site*input_ports.size()+input_index[port]; }
    template<class Visitor> void neighbors(Node u,bool reverse,Visitor visit) const {
        const Node site=u/input_ports.size();
        const auto port=input_ports[u%input_ports.size()];
        if(!reverse) {
            for(auto edge:graph.local_out(port)) {
                const int ni=graph.net_out(edge.port);
                if(ni<0) continue;
                auto moved=graph.net_move(site,ni,false);
                if(moved.site!=NONE) {
                    const auto& net=archdata::NETS[ni];
                    visit(state(moved.site,net.to),edge.delay+net.delay+moved.delay);
                }
            }
        } else {
            const int ni=graph.net_in(port);
            if(ni<0) throw std::runtime_error("Missing reverse Net for input port");
            const auto& net=archdata::NETS[ni];
            auto moved=graph.net_move(site,ni,true);
            if(moved.site==NONE) return;
            for(auto edge:graph.local_in(net.from)) {
                if(input_index[edge.port]>=0)
                    visit(state(moved.site,edge.port),edge.delay+net.delay+moved.delay);
            }
        }
    }
    void start(Node pin,bool trace=false) {
        Node site=pin/archdata::P,port=pin%archdata::P;
        if(input_index[port]>=0) {
            Node s=state(site,port);
            if(forward.improve(s,0) && trace) trace_parent[s]=NONE;
            return;
        }
        int ni=graph.net_out(port);
        if(ni>=0) {
            auto m=graph.net_move(site,ni,false);
            if(m.site!=NONE) {
                Node s=state(m.site,archdata::NETS[ni].to);
                if(forward.improve(s,m.delay+archdata::NETS[ni].delay) && trace) trace_parent[s]=NONE;
            }
            return;
        }
        for(auto edge:graph.local_out(port)) {
            ni=graph.net_out(edge.port);
            if(ni<0) continue;
            auto m=graph.net_move(site,ni,false);
            if(m.site!=NONE) {
                Node s=state(m.site,archdata::NETS[ni].to);
                if(forward.improve(s,edge.delay+m.delay+archdata::NETS[ni].delay) && trace) trace_parent[s]=NONE;
            }
        }
    }
    void finish(Node pin) {
        Node site=pin/archdata::P,port=pin%archdata::P;
        if(input_index[port]>=0) { backward.improve(state(site,port),0); return; }
        for(auto edge:graph.local_in(port))
            if(input_index[edge.port]>=0) backward.improve(state(site,edge.port),edge.delay);
    }
public:
    struct Trace {Distance delay=INF; std::vector<Node> states;};
    explicit CompactSolver(const Graph& g):graph(g),forward(g.sites()*std::size(archdata::NETS)),
                                             backward(g.sites()*std::size(archdata::NETS)) {
        input_index.fill(-1);
        for(const auto& net:archdata::NETS) {
            if(input_index[net.to]>=0) throw std::runtime_error("Inter-input port has multiple Net templates");
            input_index[net.to]=input_ports.size();
            input_ports.push_back(net.to);
        }
        if(input_ports.size()!=160) throw std::runtime_error("Unexpected inter-input count");
    }
    Distance solve(Node source,Node target,SearchStats& stats) {
        forward.reset(); backward.reset();
        if(source==target) return 0;
        Distance best=INF;
        // A query can begin on a logic Input and end on a logic Output
        // inside the same SRB without using a Net.
        if(source/archdata::P==target/archdata::P)
            for(auto edge:graph.local_out(source%archdata::P))
                if(edge.port==target%archdata::P) best=std::min(best,Distance(edge.delay));
        start(source); finish(target);
        while(!forward.empty() && !backward.empty()) {
            if(forward.top()+backward.top()>=best) break;
            const bool reverse=backward.top()<forward.top();
            Frontier& current=reverse?backward:forward;
            Frontier& other=reverse?forward:backward;
            Node u=current.pop(); ++stats.settled;
            Distance du=current.get(u);
            best=std::min(best,du+other.get(u));
            neighbors(u,reverse,[&](Node v,uint32_t weight) {
                ++stats.relaxations;
                Distance dv=du+weight;
                current.improve(v,dv);
                best=std::min(best,dv+other.get(v));
            });
        }
        return best;
    }
    Distance solve_astar(Node source,Node target,SearchStats& stats,Distance certified_upper=INF) {
        forward.reset();backward.reset();if(source==target)return 0;
        Distance best=certified_upper;
        if(source/archdata::P==target/archdata::P)for(auto edge:graph.local_out(source%archdata::P))if(edge.port==target%archdata::P)best=std::min(best,Distance(edge.delay));
        start(source);finish(target);auto target_xy=archdata::SITES[target/archdata::P];int tp=target%archdata::P;
        static const auto xgap=[] {std::array<uint64_t,archdata::WIDTH> a{};for(const auto& line:archdata::LINES)if(line.vertical)for(int x=line.site+1;x<archdata::WIDTH;++x)if(x>=0)a[x]+=line.delay;return a;}();
        static const auto ygap=[] {std::array<uint64_t,archdata::HEIGHT> a{};for(const auto& line:archdata::LINES)if(!line.vertical)for(int y=line.site+1;y<archdata::HEIGHT;++y)if(y>=0)a[y]+=line.delay;return a;}();
        auto heuristic=[&](Node node) {
            auto xy=archdata::SITES[node/input_ports.size()];int port=input_ports[node%input_ports.size()];auto phi=[](int x){return x-std::clamp(x-76,0,14);};
            int dx=phi(target_xy.x)-phi(xy.x),dy=target_xy.y-xy.y;int64_t lower=0;
            for(size_t k=0;k<4;++k) {int64_t value=int64_t(potential_lower_model::ax[k])*dx+int64_t(potential_lower_model::ay[k])*dy+potential_lower_model::distance[k*archdata::P*archdata::P+port*archdata::P+tp];lower=std::max(lower,(value+11)/12);}
            return Distance(lower)+uint64_t(std::llabs(int64_t(xgap[target_xy.x])-int64_t(xgap[xy.x])))+uint64_t(std::llabs(int64_t(ygap[target_xy.y])-int64_t(ygap[xy.y])));
        };
        struct Item {Distance f,g;Node node;bool operator<(const Item& a)const{return f>a.f || (f==a.f && node>a.node);}};
        std::priority_queue<Item> queue;
        while(!forward.empty()) {Node node=forward.pop();Distance g=forward.get(node);if(g+heuristic(node)<best)queue.push({g+heuristic(node),g,node});}
        while(!queue.empty()) {
            auto item=queue.top();queue.pop();if(item.f>=best)break;if(item.g!=forward.get(item.node))continue;++stats.settled;
            Distance terminal=backward.get(item.node);if(terminal<INF)best=std::min(best,item.g+terminal);
            neighbors(item.node,false,[&](Node next,uint32_t cost) {
                ++stats.relaxations;Distance g=item.g+cost;if(g>=best)return;Distance h=heuristic(next);if(g+h>=best)return;
                if(forward.record(next,g))queue.push({g+h,g,next});
            });
        }
        return best;
    }
    // Balanced bidirectional A*: doubled priorities avoid half-integer costs.
    // q(v)=lower(v,t)-lower(s,v); each reduced edge has cost 2w+q(v)-q(u).
    Distance solve_balanced(Node source,Node target,SearchStats& stats,Distance certified_upper=INF,double relative_error=0,Distance proposal=INF) {
        forward.reset();backward.reset();if(source==target){stats.lower=stats.upper=0;return 0;}
        Distance best=certified_upper;
        if(source/archdata::P==target/archdata::P)for(auto edge:graph.local_out(source%archdata::P))if(edge.port==target%archdata::P)best=std::min(best,Distance(edge.delay));
        start(source);finish(target);
        auto a=archdata::SITES[source/archdata::P],b=archdata::SITES[target/archdata::P];int sp=source%archdata::P,tp=target%archdata::P;
        static const auto xgap=[] {std::array<uint64_t,archdata::WIDTH> a{};for(const auto& line:archdata::LINES)if(line.vertical)for(int x=line.site+1;x<archdata::WIDTH;++x)if(x>=0)a[x]+=line.delay;return a;}();
        static const auto ygap=[] {std::array<uint64_t,archdata::HEIGHT> a{};for(const auto& line:archdata::LINES)if(!line.vertical)for(int y=line.site+1;y<archdata::HEIGHT;++y)if(y>=0)a[y]+=line.delay;return a;}();
        auto lower=[&](archdata::XY start,int p,archdata::XY end,int t) {
            auto phi=[](int x){return x-std::clamp(x-76,0,14);};int dx=phi(end.x)-phi(start.x),dy=end.y-start.y;int64_t h=0;
            for(size_t k=0;k<4;++k) {int64_t value=int64_t(potential_lower_model::ax[k])*dx+int64_t(potential_lower_model::ay[k])*dy+potential_lower_model::distance[k*archdata::P*archdata::P+p*archdata::P+t];h=std::max(h,(value+11)/12);}
            return h+std::llabs(int64_t(xgap[end.x])-int64_t(xgap[start.x]))+std::llabs(int64_t(ygap[end.y])-int64_t(ygap[start.y]));
        };
        if(balanced_potentials.empty()) {balanced_potentials.resize(graph.sites()*input_ports.size());balanced_stamps.resize(balanced_potentials.size());}
        if(++balanced_epoch==0) {std::fill(balanced_stamps.begin(),balanced_stamps.end(),0);++balanced_epoch;}
        auto potential=[&](Node u) -> int64_t {
            if(balanced_stamps[u]!=balanced_epoch) {auto xy=archdata::SITES[u/input_ports.size()];int p=input_ports[u%input_ports.size()];balanced_potentials[u]=int32_t(lower(xy,p,b,tp)-lower(a,sp,xy,p));balanced_stamps[u]=balanced_epoch;}
            return balanced_potentials[u];
        };
        struct Item {int64_t key;Distance g;Node node;bool operator<(const Item& a)const{return key>a.key || (key==a.key && node>a.node);}};
        std::priority_queue<Item> queues[2];
        while(!forward.empty()) {Node u=forward.pop();Distance g=forward.get(u);queues[0].push({2*int64_t(g)+potential(u),g,u});best=std::min(best,g+backward.get(u));}
        while(!backward.empty()) {Node u=backward.pop();Distance g=backward.get(u);queues[1].push({2*int64_t(g)-potential(u),g,u});best=std::min(best,g+forward.get(u));}
        auto clean=[&](int side) {auto& q=queues[side];auto& d=side?backward:forward;while(!q.empty() && q.top().g!=d.get(q.top().node))q.pop();};
        while(true) {
            clean(0);clean(1);if(queues[0].empty() || queues[1].empty()){stats.lower=stats.upper=best;return best;}
            int64_t sum=queues[0].top().key+queues[1].top().key;
            Distance bound=Distance(std::max<int64_t>(0,(sum+1)/2));
            if(bound>=best){stats.lower=stats.upper=best;return best;}
            if(relative_error>0 && best<INF && bound>0) {
                Distance allowance=Distance(std::floor(relative_error*double(bound)));
                if((best-bound+1)/2<=allowance) {
                    stats.lower=bound;stats.upper=best;
                    Distance low=std::max(bound,best>allowance?best-allowance:0),high=std::min(best,bound+allowance);
                    return std::clamp(proposal==INF?bound+(best-bound)/2:proposal,low,high);
                }
            }
            bool reverse=queues[1].top().key<queues[0].top().key || (queues[1].top().key==queues[0].top().key && queues[1].size()<queues[0].size());
            auto& queue=queues[reverse];auto& current=reverse?backward:forward;auto& other=reverse?forward:backward;
            auto item=queue.top();queue.pop();++stats.settled;best=std::min(best,item.g+other.get(item.node));
            int64_t qu=potential(item.node);
            neighbors(item.node,reverse,[&](Node next,uint32_t cost) {
                ++stats.relaxations;Distance g=item.g+cost;if(g>=best)return;
                int64_t qv=potential(next),reduced=2*int64_t(cost)+(reverse?qu-qv:qv-qu);
                if(reduced<0)throw std::runtime_error("Balanced potential is inconsistent with an actual edge");
                best=std::min(best,g+other.get(next));
                if(current.record(next,g))queue.push({2*int64_t(g)+(reverse?-qv:qv),g,next});
            });
        }
    }
    Distance solve_phase(Node source,Node target,SearchStats& stats,const PhaseLowerBound& phase,Distance certified_upper=INF,double relative_error=0,Distance proposal=INF,bool memo=false) {
        forward.reset();backward.reset();if(source==target){stats.lower=stats.upper=0;return 0;}
        Distance best=certified_upper;
        if(source/archdata::P==target/archdata::P)for(auto edge:graph.local_out(source%archdata::P))if(edge.port==target%archdata::P)best=std::min(best,Distance(edge.delay));
        start(source);finish(target);auto b=archdata::SITES[target/archdata::P];int tp=target%archdata::P;
        if(memo){if(phase_cached_lower.empty()){phase_cached_lower.resize(graph.sites()*input_ports.size());phase_cached_stamp.resize(phase_cached_lower.size());}if(++phase_cached_epoch==0){std::fill(phase_cached_stamp.begin(),phase_cached_stamp.end(),0);++phase_cached_epoch;}}
        auto heuristic=[&](Node u){if(memo && phase_cached_stamp[u]==phase_cached_epoch)return phase_cached_lower[u];auto h=phase.lower(archdata::SITES[u/input_ports.size()],input_ports[u%input_ports.size()],b,tp);if(memo){phase_cached_lower[u]=h;phase_cached_stamp[u]=phase_cached_epoch;}return h;};
        struct Item {Distance f,g;Node node;bool operator<(const Item& a)const{return f>a.f || (f==a.f && (g<a.g || (g==a.g && node>a.node)));}};
        std::priority_queue<Item> queue;
        while(!forward.empty()) {Node u=forward.pop();Distance g=forward.get(u);best=std::min(best,g+backward.get(u));Distance h=heuristic(u);if(g+h<best)queue.push({g+h,g,u});}
        while(!queue.empty()) {
            auto item=queue.top();queue.pop();if(item.g!=forward.get(item.node))continue;
            if(item.f>=best){stats.lower=stats.upper=best;return best;}
            if(relative_error>0 && best<INF && item.f>0) {
                Distance allowance=Distance(std::floor(relative_error*double(item.f)));
                if((best-item.f+1)/2<=allowance) {
                    stats.lower=item.f;stats.upper=best;Distance low=std::max(item.f,best>allowance?best-allowance:0),high=std::min(best,item.f+allowance);
                    return std::clamp(proposal==INF?item.f+(best-item.f)/2:proposal,low,high);
                }
            }
            ++stats.settled;best=std::min(best,item.g+backward.get(item.node));
            neighbors(item.node,false,[&](Node next,uint32_t cost) {
                ++stats.relaxations;
                Distance g=item.g+cost;if(g>=best)return;best=std::min(best,g+backward.get(next));Distance h=heuristic(next);if(g+h>=best)return;
                if(forward.record(next,g))queue.push({g+h,g,next});
            });
        }
        stats.lower=stats.upper=best;return best;
    }
    // Weighted priority returns feasible upper paths, not an error certificate.
    Distance solve_phase_weighted(Node source,Node target,SearchStats& stats,const PhaseLowerBound& phase,Distance certified_upper=INF,double weight=1.05) {
        forward.reset();backward.reset();if(source==target){stats.lower=stats.upper=0;return 0;}
        Distance best=certified_upper;
        if(source/archdata::P==target/archdata::P)for(auto edge:graph.local_out(source%archdata::P))if(edge.port==target%archdata::P)best=std::min(best,Distance(edge.delay));
        start(source);finish(target);auto b=archdata::SITES[target/archdata::P];int tp=target%archdata::P;
        auto heuristic=[&](Node u){return phase.lower(archdata::SITES[u/input_ports.size()],input_ports[u%input_ports.size()],b,tp);};
        struct Item {Distance f,g;Node node;bool operator<(const Item& a)const{return f>a.f || (f==a.f && (g<a.g || (g==a.g && node>a.node)));}};
        std::priority_queue<Item> queue;
        while(!forward.empty()) {Node u=forward.pop();Distance g=forward.get(u);best=std::min(best,g+backward.get(u));Distance h=Distance(std::ceil(weight*heuristic(u)));if(g+h<best)queue.push({g+h,g,u});}
        while(!queue.empty()) {
            auto item=queue.top();queue.pop();if(item.g!=forward.get(item.node))continue;
            if(item.f>=best){stats.upper=best;return best;}
            ++stats.settled;best=std::min(best,item.g+backward.get(item.node));
            neighbors(item.node,false,[&](Node next,uint32_t cost) {
                ++stats.relaxations;
                Distance g=item.g+cost;if(g>=best)return;best=std::min(best,g+backward.get(next));Distance h=Distance(std::ceil(weight*heuristic(next)));if(g+h>=best)return;
                if(forward.record(next,g))queue.push({g+h,g,next});
            });
        }
        stats.upper=best;return best;
    }
    Trace trace(Node source,Node target,SearchStats& stats) {
        forward.reset();
        if(trace_parent.empty()) trace_parent.resize(graph.sites()*input_ports.size(),NONE);
        if(source==target) return {0,{}};
        Distance best=INF;
        Node terminal=NONE;
        const Node target_site=target/archdata::P;
        const int target_port=target%archdata::P;
        if(source/archdata::P==target_site)
            for(auto edge:graph.local_out(source%archdata::P))
                if(edge.port==target_port) best=std::min(best,Distance(edge.delay));
        start(source,true);
        while(!forward.empty() && forward.top()<best) {
            Node u=forward.pop(); ++stats.settled;
            Distance du=forward.get(u);
            if(u/input_ports.size()==target_site) {
                const int port=input_ports[u%input_ports.size()];
                if(port==target_port && du<best) {best=du;terminal=u;}
                for(auto edge:graph.local_out(port))
                    if(edge.port==target_port && du+edge.delay<best) {
                        best=du+edge.delay;terminal=u;
                    }
            }
            if(du>=best) continue;
            neighbors(u,false,[&](Node v,uint32_t weight) {
                ++stats.relaxations;
                if(forward.improve(v,du+weight)) trace_parent[v]=u;
            });
        }
        Trace result;result.delay=best;
        while(terminal!=NONE) {
            result.states.push_back(terminal);
            terminal=trace_parent[terminal];
        }
        std::reverse(result.states.begin(),result.states.end());
        return result;
    }
    Node trace_site(Node state) const {return state/input_ports.size();}
    unsigned trace_port(Node state) const {return input_ports[state%input_ports.size()];}
};

