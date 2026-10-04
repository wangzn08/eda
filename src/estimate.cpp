#include "architecture_data.hpp"
#include "lookup_model.hpp"
#include "spatial_model.hpp"
#include "port_model.hpp"
#include "source_x_model.hpp"
#include "target_x_model.hpp"
#include "dx_model.hpp"
#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
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

struct SearchStats {uint64_t settled=0, relaxations=0;};

// Offline-fitted, constant-time approximate oracle. All inputs are public
// architecture constants and the request endpoints; no labels are read here.
Distance lookup_delay(Node source,Node target) {
    if(source==target) return 0;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=b.x-a.x,dy=b.y-a.y;
    int sx=(dx>0)-(dx<0),sy=(dy>0)-(dy<0);
    size_t key=(((sx+1)*3+(sy+1))*15+std::abs(dx)/8)*35+std::abs(dy)/16;
    double estimate=lookup_model::intercept+lookup_model::ax*std::abs(dx)
        +lookup_model::ay*std::abs(dy)+lookup_model::residual[key]
        +lookup_model::source[source%archdata::P]+lookup_model::target[target%archdata::P];
    estimate=std::max(0.0,std::nearbyint(estimate));
    for(const auto& line:archdata::LINES) {
        int u=line.vertical?a.x:a.y,v=line.vertical?b.x:b.y;
        if(std::min(u,v)<=line.site && line.site<std::max(u,v)) estimate+=lookup_model::line[line.id];
    }
    for(const auto& block:archdata::BLOCKS) {
        if(std::max(a.x,b.x)>=block.left && std::min(a.x,b.x)<=block.right
           && std::max(a.y,b.y)>=block.lower && std::min(a.y,b.y)<=block.upper)
            estimate+=lookup_model::block[block.id];
    }
    return static_cast<Distance>(std::max(0.0,std::nearbyint(estimate)));
}

Distance spatial_delay(Node source,Node target) {
    Distance base=lookup_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int xsign=(b.x>a.x)-(b.x<a.x),ysign=(b.y>a.y)-(b.y<a.y);
    const size_t xkey=((a.x/10)*12+(b.x/10))*3+ysign+1;
    const size_t ykey=((a.y/50)*11+(b.y/50))*3+xsign+1;
    double estimate=base+spatial_model::x_pair[xkey]+spatial_model::y_pair[ykey];
    return static_cast<Distance>(std::max(0.0,std::nearbyint(estimate)));
}

Distance port_delay(Node source,Node target) {
    Distance base=spatial_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=(b.x>a.x)-(b.x<a.x),dy=(b.y>a.y)-(b.y<a.y);
    int from=port_model::family[source%archdata::P];
    int to=port_model::family[target%archdata::P];
    size_t key=((from*port_model::FAMILIES+to)*3+dx+1)*3+dy+1;
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+port_model::residual[key])));
}

Distance source_x_delay(Node source,Node target) {
    Distance base=port_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=(b.x>a.x)-(b.x<a.x),dy=(b.y>a.y)-(b.y<a.y);
    int from=port_model::family[source%archdata::P];
    size_t key=((from*120+a.x)*3+dx+1)*3+dy+1;
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+source_x_model::residual[key])));
}

Distance target_x_delay(Node source,Node target) {
    Distance base=source_x_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=(b.x>a.x)-(b.x<a.x),dy=(b.y>a.y)-(b.y<a.y);
    int to=port_model::family[target%archdata::P];
    size_t key=((to*120+b.x)*3+dx+1)*3+dy+1;
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+target_x_model::residual[key])));
}

Distance v2_delay(Node source,Node target) {
    Distance base=target_x_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=b.x-a.x,ysign=(b.y>a.y)-(b.y<a.y);
    size_t key=(dx+119)*3+ysign+1;
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+dx_model::residual[key])));
}
class Solver {
    const Graph& graph;
    Frontier forward,backward;
public:
    explicit Solver(const Graph& g):graph(g),forward(g.nodes()),backward(g.nodes()) {}
    Distance solve(Node s,Node t,bool bidirectional,SearchStats& stats) {
        forward.reset(); backward.reset();
        if(s==t) return 0;
        forward.improve(s,0);
        if(!bidirectional) {
            while(!forward.empty()) {
                Node u=forward.pop(); ++stats.settled;
                if(u==t) return forward.get(u);
                graph.neighbors(u,false,[&](Node v,uint32_t weight) {
                    ++stats.relaxations; forward.improve(v,forward.get(u)+weight);
                });
            }
            return INF;
        }
        backward.improve(t,0);
        Distance best=INF;
        while(!forward.empty() && !backward.empty()) {
            if(forward.top()+backward.top()>=best) break;
            bool reverse=backward.top()<forward.top();
            Frontier& current=reverse?backward:forward;
            Frontier& other=reverse?forward:backward;
            Node u=current.pop(); ++stats.settled;
            Distance du=current.get(u);
            best=std::min(best,du+other.get(u));
            graph.neighbors(u,reverse,[&](Node v,uint32_t weight) {
                ++stats.relaxations;
                Distance dv=du+weight;
                current.improve(v,dv);
                best=std::min(best,dv+other.get(v));
            });
        }
        return best;
    }
};

// Arc edges always go Input -> Output; Net edges always Output -> Input.
// Interior vertices can therefore be reduced to 160 inter-SRB Input ports.
class CompactSolver {
    const Graph& graph;
    std::array<int,archdata::P> input_index;
    std::vector<uint16_t> input_ports;
    Frontier forward,backward;
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
    void start(Node pin) {
        Node site=pin/archdata::P,port=pin%archdata::P;
        if(input_index[port]>=0) { forward.improve(state(site,port),0); return; }
        int ni=graph.net_out(port);
        if(ni>=0) {
            auto m=graph.net_move(site,ni,false);
            if(m.site!=NONE) forward.improve(state(m.site,archdata::NETS[ni].to),m.delay+archdata::NETS[ni].delay);
            return;
        }
        for(auto edge:graph.local_out(port)) {
            ni=graph.net_out(edge.port);
            if(ni<0) continue;
            auto m=graph.net_move(site,ni,false);
            if(m.site!=NONE) forward.improve(state(m.site,archdata::NETS[ni].to),edge.delay+m.delay+archdata::NETS[ni].delay);
        }
    }
    void finish(Node pin) {
        Node site=pin/archdata::P,port=pin%archdata::P;
        if(input_index[port]>=0) { backward.improve(state(site,port),0); return; }
        for(auto edge:graph.local_in(port))
            if(input_index[edge.port]>=0) backward.improve(state(site,edge.port),edge.delay);
    }
public:
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
};

std::string trim(std::string s) {
    auto a=s.find_first_not_of(" \t\r\n"), b=s.find_last_not_of(" \t\r\n");
    return a==std::string::npos?"":s.substr(a,b-a+1);
}

std::string_view trim_view(std::string_view s) {
    auto first=s.find_first_not_of(" \t\r\n"),last=s.find_last_not_of(" \t\r\n");
    return first==s.npos?std::string_view{}:s.substr(first,last-first+1);
}

int main(int argc,char** argv) {
    try {
        std::string input,output,stats_path,algorithm="port";
        for(int i=1;i<argc;++i) {
            std::string arg=argv[i];
            if(arg=="--help") {
                std::cout<<"estimate -in requests.csv -out results.csv [--algorithm bidirectional|dijkstra|compressed|approximate|spatial|port|source-x|target-x|v2] [--stats stats.csv]\n";return 0;
            }
            if(i+1>=argc) throw std::runtime_error("Missing argument value");
            if(arg=="-in") input=argv[++i];
            else if(arg=="-out") output=argv[++i];
            else if(arg=="--stats") stats_path=argv[++i];
            else if(arg=="--algorithm") algorithm=argv[++i];
            else throw std::runtime_error("Unknown option: "+arg);
        }
        if(input.empty() || output.empty() || input==output) throw std::runtime_error("Provide distinct -in and -out files");
        if(!stats_path.empty() && (stats_path==input || stats_path==output)) throw std::runtime_error("Stats file must differ from input/output");
        if(algorithm!="bidirectional" && algorithm!="dijkstra" && algorithm!="compressed" && algorithm!="approximate" && algorithm!="spatial" && algorithm!="port" && algorithm!="source-x" && algorithm!="target-x" && algorithm!="v2") throw std::runtime_error("Unknown algorithm");
        std::ifstream in(input);
        if(!in) throw std::runtime_error("Cannot open input");
        std::string header;
        std::getline(in,header);
        if(trim(header)!="From,To") throw std::runtime_error("Expected input header From,To (no golden column)");
        std::vector<char> output_buffer(1<<20);
        std::ofstream out, stats;
        out.rdbuf()->pubsetbuf(output_buffer.data(),output_buffer.size());
        out.open(output);
        if(!out) throw std::runtime_error("Cannot open output");
        if(!stats_path.empty()) {
            stats.open(stats_path);
            if(!stats) throw std::runtime_error("Cannot open stats file");
            stats<<"row,delay,wall_ms,settled,relaxations\n";
        }
        const auto cpu_start=std::clock();
        const bool fast=algorithm=="approximate" || algorithm=="spatial" || algorithm=="port" || algorithm=="source-x" || algorithm=="target-x" || algorithm=="v2";
        FastPinParser parser;
        std::unique_ptr<Graph> graph;
        if(!fast) graph=std::make_unique<Graph>();
        std::unique_ptr<Solver> solver;
        std::unique_ptr<CompactSolver> compact_solver;
        if(algorithm=="compressed") compact_solver=std::make_unique<CompactSolver>(*graph);
        else if(!fast) solver=std::make_unique<Solver>(*graph);
        out<<"From,To,delay\n";
        std::string line; uint64_t row=0;
        while(std::getline(in,line)) {
            auto record=trim_view(line);
            if(record.empty()) continue;
            auto comma=record.find(',');
            if(comma==record.npos || record.find(',',comma+1)!=record.npos) throw std::runtime_error("Invalid CSV row");
            std::string_view s=trim_view(record.substr(0,comma)),t=trim_view(record.substr(comma+1));
            const bool collect=stats.is_open();
            auto start=collect?std::chrono::steady_clock::now():std::chrono::steady_clock::time_point{};
            SearchStats counters;
            Node from=parser.pin(s),to=parser.pin(t);
            Distance d=algorithm=="approximate"?lookup_delay(from,to):
                algorithm=="spatial"?spatial_delay(from,to):
                algorithm=="port"?port_delay(from,to):
                algorithm=="source-x"?source_x_delay(from,to):
                algorithm=="target-x"?target_x_delay(from,to):
                algorithm=="v2"?v2_delay(from,to):
                compact_solver?compact_solver->solve(from,to,counters):solver->solve(from,to,algorithm=="bidirectional",counters);
            if(d>=INF) throw std::runtime_error("Unreachable query: "+std::string(s)+" -> "+std::string(t)+"; official output convention unspecified");
            out.write(s.data(),s.size());out.put(',');out.write(t.data(),t.size());out.put(',');
            char digits[32];auto end=std::to_chars(digits,digits+sizeof(digits),d);
            if(end.ec!=std::errc()) throw std::runtime_error("Cannot format delay");
            out.write(digits,end.ptr-digits);out.put('\n');
            ++row;
            if(collect) {
                auto ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
                stats<<row<<','<<d<<','<<ms<<','<<counters.settled<<','<<counters.relaxations<<'\n';
                stats.flush();
            }
        }
        out.flush();
        if(in.bad() || !out || (stats.is_open() && !stats)) throw std::runtime_error("File I/O failed");
        std::cerr<<"rows="<<row<<" cpu_seconds="<<double(std::clock()-cpu_start)/CLOCKS_PER_SEC<<" arch_sha256="<<archdata::HASH<<'\n';
        return 0;
    } catch(const std::exception& e) { std::cerr<<"error: "<<e.what()<<'\n'; return 1; }
}
