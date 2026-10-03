#include "architecture_data.hpp"
#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Node = uint32_t;
using Distance = uint64_t;
constexpr Node NONE = std::numeric_limits<Node>::max();
constexpr Node SETTLED = NONE - 1;
constexpr Distance INF = std::numeric_limits<Distance>::max()/4;

struct Move { Node site=NONE; uint32_t delay=0; };
struct LocalEdge { uint16_t port; uint32_t delay; };

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

std::string trim(std::string s) {
    auto a=s.find_first_not_of(" \t\r\n"), b=s.find_last_not_of(" \t\r\n");
    return a==std::string::npos?"":s.substr(a,b-a+1);
}

int main(int argc,char** argv) {
    try {
        std::string input,output,stats_path,algorithm="bidirectional";
        for(int i=1;i<argc;++i) {
            std::string arg=argv[i];
            if(arg=="--help") {
                std::cout<<"estimate -in requests.csv -out results.csv [--algorithm bidirectional|dijkstra] [--stats stats.csv]\n";return 0;
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
        if(algorithm!="bidirectional" && algorithm!="dijkstra") throw std::runtime_error("Unknown algorithm");
        std::ifstream in(input);
        if(!in) throw std::runtime_error("Cannot open input");
        std::string header;
        std::getline(in,header);
        if(trim(header)!="From,To") throw std::runtime_error("Expected input header From,To (no golden column)");
        std::ofstream out(output), stats;
        if(!out) throw std::runtime_error("Cannot open output");
        if(!stats_path.empty()) {
            stats.open(stats_path);
            if(!stats) throw std::runtime_error("Cannot open stats file");
            stats<<"row,delay,wall_ms,settled,relaxations\n";
        }
        const auto cpu_start=std::clock();
        Graph graph; Solver solver(graph);
        out<<"From,To,delay\n";
        std::string line; uint64_t row=0;
        while(std::getline(in,line)) {
            line=trim(line);
            if(line.empty()) continue;
            auto comma=line.find(',');
            if(comma==std::string::npos || line.find(',',comma+1)!=std::string::npos) throw std::runtime_error("Invalid CSV row");
            std::string s=trim(line.substr(0,comma)),t=trim(line.substr(comma+1));
            auto start=std::chrono::steady_clock::now();
            SearchStats counters;
            Distance d=solver.solve(graph.pin(s),graph.pin(t),algorithm=="bidirectional",counters);
            if(d>=INF) throw std::runtime_error("Unreachable query: "+s+" -> "+t+"; official output convention unspecified");
            auto ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
            out<<s<<','<<t<<','<<d<<'\n';
            ++row;
            if(stats.is_open()) { stats<<row<<','<<d<<','<<ms<<','<<counters.settled<<','<<counters.relaxations<<'\n'; stats.flush(); }
        }
        out.flush();
        if(in.bad() || !out || (stats.is_open() && !stats)) throw std::runtime_error("File I/O failed");
        std::cerr<<"rows="<<row<<" cpu_seconds="<<double(std::clock()-cpu_start)/CLOCKS_PER_SEC<<" arch_sha256="<<archdata::HASH<<'\n';
        return 0;
    } catch(const std::exception& e) { std::cerr<<"error: "<<e.what()<<'\n'; return 1; }
}
