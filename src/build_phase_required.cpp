// Exact shortest distances in periodic, architecture-derived relaxed graphs.
#include "architecture_data.hpp"
#include "potential_lower_model.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <queue>
#include <vector>
#include <ctime>
struct Edge {int from,to,dx,dy,cost;};
int main(int argc,char** argv) {
    try {
        if(argc!=2)throw std::runtime_error("build_phase_bounds output.bin");
        std::array<int,archdata::P> index;index.fill(-1);std::vector<int> ports;
        for(const auto& n:archdata::NETS) {if(index[n.to]>=0)throw std::runtime_error("Duplicate input");index[n.to]=ports.size();ports.push_back(n.to);}
        std::vector<std::vector<Edge>> incoming(ports.size());
        for(const auto& arc:archdata::ARCS)if(index[arc.from]>=0)for(const auto& net:archdata::NETS)if(net.from==arc.to) {
            auto v=archdata::VECTORS[net.vector];incoming[index[net.to]].push_back({index[arc.from],index[net.to],v.x,v.y,12*int(arc.delay+net.delay)});
        }
        std::ofstream file(argv[1],std::ios::binary);if(!file)throw std::runtime_error("Cannot open output");
        file.write("PHASYREQ",8);uint32_t header[]={1,archdata::P,uint32_t(ports.size()),4,10,10,12};file.write(reinterpret_cast<char*>(header),sizeof(header));
        std::vector<uint16_t> encoded_ports(ports.begin(),ports.end());file.write(reinterpret_cast<char*>(encoded_ports.data()),2*ports.size());
        auto start=std::clock();uint64_t negative=0,unreachable=0;int minimum=0,maximum=0;
        int block_delay=1000000000;
        for(const auto& block:archdata::BLOCKS)if(block.hcross) {if(block.left!=76 || block.right!=89 || block.vcross)throw std::runtime_error("Unsupported crossing geometry");block_delay=std::min(block_delay,block.hdelay);}
        if(block_delay==1000000000)throw std::runtime_error("Missing horizontal crossing strip");
        for(int mode=1;mode<2;++mode)for(int k=0;k<4;++k)for(int tp=0;tp<archdata::P;++tp) {
            int px=10,phases=px*12,base_states=int(ports.size())*phases,states=base_states*2;const int inf=1000000000;
            auto mod=[](int v,int p){return (v%p+p)%p;};std::vector<int> d(states,inf);
            auto folded=[&](int p){return int(potential_lower_model::distance[k*archdata::P*archdata::P+ports[p]*archdata::P+tp]);};
            using Item=std::pair<int,int>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
            auto seed=[&](int p,int cost){int node=p*phases;if(cost<d[node]) {d[node]=cost;queue.emplace(cost,node);}};
            if(index[tp]>=0)seed(index[tp],-folded(index[tp]));
            for(const auto& arc:archdata::ARCS)if(arc.to==tp && index[arc.from]>=0)seed(index[arc.from],12*int(arc.delay)-folded(index[arc.from]));
            while(!queue.empty()) {
                auto item=queue.top();int g=item.first,u=item.second;queue.pop();if(g!=d[u])continue;int flag=u/base_states,local=u%base_states,port=local/phases,x=(local%phases)/12,y=local%12;
                for(const auto& edge:incoming[port]) {
                    int potential=edge.dx?potential_lower_model::ax[k]*edge.dx:potential_lower_model::ay[k]*edge.dy;
                    int cost=edge.cost-potential+folded(edge.to)-folded(edge.from);if(cost<0) {++negative;throw std::runtime_error("Non-feasible port reweighting");}
                    auto relax=[&](int dx,int extra) {int next_flag=flag || std::abs(edge.dy)>=12;int node=next_flag*base_states+edge.from*phases+mod(x-dx,px)*12+mod(y-edge.dy,12),value=g+cost+extra;if(value<d[node]){d[node]=value;queue.emplace(value,node);}};
                    relax(edge.dx,0);
                    if(mode==1 && edge.dx)relax(edge.dx+(edge.dx>0?14:-14),12*block_delay-potential_lower_model::ax[k]*(edge.dx>0?14:-14));
                }
            }
            std::vector<int16_t> encoded(base_states);
            for(int p=0;p<int(ports.size());++p)for(int phase=0;phase<phases;++phase) {
                int value=d[base_states+p*phases+phase];if(value==inf) {++unreachable;value=32767;}else value+=folded(p);
                minimum=std::min(minimum,value);maximum=std::max(maximum,value);if(value<-32768)throw std::runtime_error("Lower encoding overflow");encoded[p*phases+phase]=int16_t(std::min(value,32767));
            }
            file.write(reinterpret_cast<char*>(encoded.data()),encoded.size()*2);
            if(tp%64==0)std::cerr<<"mode="<<mode<<" px="<<px<<" slope="<<k<<" target="<<tp<<" cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';
        }
        if(!file)throw std::runtime_error("Output failure");std::cerr<<"complete min="<<minimum<<" max="<<maximum<<" unreachable="<<unreachable<<" negative_edges="<<negative<<" cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
