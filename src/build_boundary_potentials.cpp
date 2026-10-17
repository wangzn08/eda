// Four directional min-plus mobility potentials on the actual geometry.
// Subtract signed Line potentials to remove monotone tolls already in the base
// predictor. Non-monotone crossings and unavailable moves remain in the field.
#include "routing_search.hpp"
#include <fstream>
#include <iostream>
#include <ctime>
struct PotentialEdge{uint16_t core,vector,net;int32_t cost,dx,dy;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("Potential raw output required");Graph graph;
 std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);unsigned count=0;
 for(unsigned i=0;i<std::size(archdata::NETS);++i){auto n=archdata::NETS[i];index[n.to]=count++;netout[n.from]=i;}if(count!=160)throw std::runtime_error("Core count");
 std::array<std::vector<PotentialEdge>,160>forward,reverse;
 for(auto a:archdata::ARCS)if(index[a.from]>=0 && netout[a.to]>=0){int ni=netout[a.to];auto n=archdata::NETS[ni];auto v=archdata::VECTORS[n.vector];int u=index[a.from],t=index[n.to];forward[u].push_back({uint16_t(t),uint16_t(n.vector),uint16_t(ni),a.delay+n.delay,v.x,v.y});reverse[t].push_back({uint16_t(u),uint16_t(n.vector),uint16_t(ni),a.delay+n.delay,-v.x,-v.y});}
 std::array<int,120>xgap{};std::array<int,550>ygap{};for(auto l:archdata::LINES){if(l.vertical)for(int x=l.site+1;x<120;++x)xgap[x]+=l.delay;else for(int y=l.site+1;y<550;++y)ygap[y]+=l.delay;}
 constexpr int large=100000000;size_t n=std::size(archdata::SITES)*160;std::vector<std::array<int32_t,4>>previous(n),next(n);std::array<std::array<int32_t,4>,160>ideal{},ideal_next{};
 const int wx[4]={750,750,-750,-750},wy[4]={635,-625,635,-625},sx[4]={1,1,-1,-1},sy[4]={1,-1,1,-1};
 std::ofstream f(argv[1],std::ios::binary);f.write("PHIPEN01",8);f.write(archdata::HASH,64);uint32_t shape[5]={2,3,uint32_t(std::size(archdata::SITES)),160,4};f.write(reinterpret_cast<char*>(shape),20);auto begin=std::clock();
 for(unsigned mode=0;mode<2;++mode){for(auto&v:previous)v.fill(0);for(auto&v:ideal)v.fill(0);auto&edges=mode?reverse:forward;
  for(unsigned depth=1;depth<=4;++depth){for(unsigned p=0;p<160;++p){ideal_next[p].fill(large);for(auto e:edges[p])for(unsigned k=0;k<4;++k)ideal_next[p][k]=std::min(ideal_next[p][k],e.cost*60-wx[k]*e.dx-wy[k]*e.dy+ideal[e.core][k]);}
   for(Node site=0;site<std::size(archdata::SITES);++site){auto a=archdata::SITES[site];for(unsigned p=0;p<160;++p){auto&out=next[size_t(site)*160+p];out.fill(large);for(auto e:edges[p]){Move m=mode?graph.net_move(site,e.net,true):graph.forward_vector_move(site,e.vector);if(m.site==NONE)continue;auto b=archdata::SITES[m.site];const auto&tail=previous[size_t(m.site)*160+e.core];int dx=b.x-a.x,dy=b.y-a.y,gx=xgap[b.x]-xgap[a.x],gy=ygap[b.y]-ygap[a.y];for(unsigned k=0;k<4;++k){if(tail[k]>=large)continue;int value=(e.cost+int(m.delay))*60-wx[k]*dx-wy[k]*dy-60*(sx[k]*gx+sy[k]*gy)+tail[k];out[k]=std::min(out[k],value);}}}}
   previous.swap(next);ideal=ideal_next;
   if(depth==1||depth==2||depth==4){std::vector<int16_t>row(160*4);uint64_t negative=0,clipped=0;for(Node site=0;site<std::size(archdata::SITES);++site){for(unsigned p=0;p<160;++p)for(unsigned k=0;k<4;++k){int difference=previous[size_t(site)*160+p][k]-ideal[p][k];if(difference<0)++negative;if(difference%5)throw std::runtime_error("Potential scale");int value=difference/5;if(value<0||value>32767)++clipped;row[p*4+k]=int16_t(std::clamp(value,0,32767));}f.write(reinterpret_cast<char*>(row.data()),row.size()*2);}std::cerr<<"mode="<<mode<<" depth="<<depth<<" negative="<<negative<<" clipped="<<clipped<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';}
  }
 }
 if(!f)throw std::runtime_error("Potential output");std::cerr<<"bytes="<<uint64_t(f.tellp())<<'\n';
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
