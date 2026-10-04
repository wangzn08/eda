// Offline path-witness database for the translation-invariant SRB graph.
// We retain a feasible path cost and its bounding box, not public answers.
#include "architecture_data.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <vector>

constexpr uint32_t infinity=std::numeric_limits<uint32_t>::max()/4;
struct Box {int16_t left=0,right=0,lower=0,upper=0;uint16_t variation_x=0,variation_y=0;};
struct Edge {uint16_t to; int16_t dx,dy; uint32_t cost;};
struct Entry {uint32_t packed;};
static_assert(sizeof(Entry)==4);

int main(int argc,char** argv) {
    try {
        if(argc!=6) throw std::runtime_error("local_oracle_build ports.txt output.bin local_x local_y patch_radius");
        const int lx=std::stoi(argv[3]),ly=std::stoi(argv[4]),radius=std::stoi(argv[5]);
        if(lx<0 || ly<0 || radius<std::max(lx,ly)+12 || radius>100)
            throw std::runtime_error("Invalid patch geometry");
        std::ifstream ports(argv[1]);
        unsigned ns=0,nt=0;ports>>ns>>nt;
        if(!ports || !ns || !nt || ns>archdata::P || nt>archdata::P) throw std::runtime_error("Invalid ports file");
        std::vector<uint16_t> sources(ns),targets(nt);
        for(auto& p:sources){unsigned v;ports>>v;if(!ports || v>=archdata::P) throw std::runtime_error("Invalid source port");p=v;}
        for(auto& p:targets){unsigned v;ports>>v;if(!ports || v>=archdata::P) throw std::runtime_error("Invalid target port");p=v;}
        std::array<int,archdata::P> input,net_from;
        input.fill(-1);net_from.fill(-1);
        unsigned inputs=0;
        for(size_t i=0;i<std::size(archdata::NETS);++i) {
            const auto& n=archdata::NETS[i];
            if(input[n.to]>=0 || net_from[n.from]>=0) throw std::runtime_error("Nonunique Net");
            input[n.to]=inputs++;net_from[n.from]=i;
        }
        std::array<std::vector<archdata::Arc>,archdata::P> outgoing,incoming;
        std::vector<std::vector<Edge>> edges(inputs);
        for(const auto& a:archdata::ARCS) {
            if(a.delay<0) throw std::runtime_error("Negative Arc");
            outgoing[a.from].push_back(a);incoming[a.to].push_back(a);
            if(input[a.from]>=0 && net_from[a.to]>=0) {
                const auto& n=archdata::NETS[net_from[a.to]];
                const auto& v=archdata::VECTORS[n.vector];
                edges[input[a.from]].push_back({uint16_t(input[n.to]),int16_t(v.x),int16_t(v.y),uint32_t(a.delay+n.delay)});
            }
        }
        const int width=2*radius+1;
        const size_t states=size_t(width)*width*inputs;
        const auto state=[&](int x,int y,unsigned p){return uint32_t(((x+radius)*width+y+radius)*inputs+p);};
        std::vector<uint32_t> dist(states);
        std::vector<Box> boxes(states);
        std::ofstream out(argv[2],std::ios::binary);
        if(!out) throw std::runtime_error("Cannot open output");
        out.write("LOCORC1\0",8);
        const std::array<uint32_t,6> header={4,uint32_t(lx),uint32_t(ly),ns,nt,uint32_t(radius)};
        out.write(reinterpret_cast<const char*>(header.data()),sizeof(header));
        out.write(reinterpret_cast<const char*>(sources.data()),sources.size()*2);
        out.write(reinterpret_cast<const char*>(targets.data()),targets.size()*2);
        uint64_t valid=0,missing=0;
        for(unsigned si=0;si<ns;++si) {
            const unsigned source=sources[si];
            std::fill(dist.begin(),dist.end(),infinity);
            std::priority_queue<uint64_t,std::vector<uint64_t>,std::greater<uint64_t>> queue;
            const auto improve=[&](int x,int y,unsigned p,uint32_t value,Box box) {
                if(x < -radius || x > radius || y < -radius || y > radius) return;
                const uint32_t s=state(x,y,p);
                if(value>=dist[s]) return;
                box.left=std::min<int>(box.left,x);box.right=std::max<int>(box.right,x);
                box.lower=std::min<int>(box.lower,y);box.upper=std::max<int>(box.upper,y);
                dist[s]=value;boxes[s]=box;queue.push((uint64_t(value)<<32)|s);
            };
            if(input[source]>=0) improve(0,0,input[source],0,{});
            else if(net_from[source]>=0) {
                const auto& n=archdata::NETS[net_from[source]];const auto& v=archdata::VECTORS[n.vector];
                Box box;box.variation_x=std::abs(v.x);box.variation_y=std::abs(v.y);
                improve(v.x,v.y,input[n.to],n.delay,box);
            } else for(const auto& a:outgoing[source]) if(net_from[a.to]>=0) {
                const auto& n=archdata::NETS[net_from[a.to]];const auto& v=archdata::VECTORS[n.vector];
                Box box;box.variation_x=std::abs(v.x);box.variation_y=std::abs(v.y);
                improve(v.x,v.y,input[n.to],a.delay+n.delay,box);
            }
            while(!queue.empty()) {
                const uint64_t item=queue.top();queue.pop();
                const uint32_t s=uint32_t(item),value=uint32_t(item>>32);
                if(value!=dist[s]) continue;
                const int site=s/inputs,x=site/width-radius,y=site%width-radius;
                for(const auto& e:edges[s%inputs]) {
                    Box next=boxes[s];next.variation_x+=std::abs(e.dx);next.variation_y+=std::abs(e.dy);
                    improve(x+e.dx,y+e.dy,e.to,value+e.cost,next);
                }
            }
            std::vector<Entry> row(size_t(2*lx+1)*(2*ly+1)*nt);
            for(int dy=-ly;dy<=ly;++dy) for(int dx=-lx;dx<=lx;++dx) {
                for(unsigned ti=0;ti<nt;++ti) {
                    const unsigned target=targets[ti];uint32_t best=infinity;Box box;
                    if(input[target]>=0) {const auto s=state(dx,dy,input[target]);best=dist[s];box=boxes[s];}
                    else for(const auto& a:incoming[target]) if(input[a.from]>=0) {
                        const auto s=state(dx,dy,input[a.from]);
                        if(dist[s]<infinity && dist[s]+a.delay<best) {best=dist[s]+a.delay;box=boxes[s];}
                    }
                    if(dx==0 && dy==0) {
                        if(source==target){best=0;box={};}
                        for(const auto& a:outgoing[source]) if(unsigned(a.to)==target && uint32_t(a.delay)<best) {best=a.delay;box={};}
                    }
                    const int left=std::min(0,dx)-box.left,right=box.right-std::max(0,dx);
                    const int lower=std::min(0,dy)-box.lower,upper=box.upper-std::max(0,dy);
                    Entry result{16383};
                    if(best<16383 && left>=0 && right>=0 && lower>=0 && upper>=0 && std::max({left,right,lower,upper})<=15) {
                        // The minimum variation compatible with this bounding box
                        // proves each gap is crossed once inside the direct span,
                        // twice in an excursion, and zero times outside the box.
                        const bool simple_x=box.variation_x==std::abs(dx)+2*(left+right);
                        const bool simple_y=box.variation_y==std::abs(dy)+2*(lower+upper);
                        result={best|(uint32_t(left)<<14)|(uint32_t(right)<<18)|
                            (uint32_t(lower)<<22)|(uint32_t(upper)<<26)|
                            (uint32_t(simple_x)<<30)|(uint32_t(simple_y)<<31)};++valid;
                    } else ++missing;
                    row[((dy+ly)*(2*lx+1)+dx+lx)*nt+ti]=result;
                }
            }
            out.write(reinterpret_cast<const char*>(row.data()),row.size()*sizeof(Entry));
            if(!out) throw std::runtime_error("Output write failed");
            std::cout<<"source="<<si+1<<"/"<<ns<<" valid="<<valid<<" missing="<<missing<<'\n'<<std::flush;
        }
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
