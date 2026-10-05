// Architecture-only finite-window shortest paths for an extrapolation experiment.
#include "architecture_data.hpp"
#include <array>
#include <algorithm>
#include <vector>
#include <fstream>
#include <iostream>
#include <limits>
#include <ctime>
struct E {int to,dx,dy,cost;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("build_periodic_anchor output.bin");
 std::array<int,496> index,netout;index.fill(-1);netout.fill(-1);std::vector<uint16_t> ports;
 for(int i=0;i<int(std::size(archdata::NETS));++i){auto n=archdata::NETS[i];index[n.to]=ports.size();ports.push_back(n.to);netout[n.from]=i;}
 std::vector<std::vector<E>> edges(160);std::array<std::vector<archdata::Arc>,496> incoming;
 for(auto a:archdata::ARCS){incoming[a.to].push_back(a);if(index[a.from]>=0 && netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay});}}
 constexpr int R=48,W=97,limit=4096;auto state=[](int x,int y,int p){return ((x+R)*W+y+R)*160+p;};
 std::vector<uint16_t>d(W*W*160);std::vector<std::vector<uint32_t>> buckets(limit);
 std::ofstream out(argv[1],std::ios::binary);out.write("ANCHOR01",8);out.write(archdata::HASH,64);out.write(reinterpret_cast<char*>(ports.data()),320);
 auto begin=std::clock();
 for(int si=0;si<160;++si){std::fill(d.begin(),d.end(),65535);for(auto& b:buckets)b.clear();d[state(0,0,si)]=0;buckets[0].push_back(state(0,0,si));
  for(int cost=0;cost<limit;++cost)for(size_t at=0;at<buckets[cost].size();++at){auto u=buckets[cost][at];if(d[u]!=cost)continue;int x=int(u/160)/W-R,y=int(u/160)%W-R;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -R || nx>R || ny < -R || ny>R || value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value].push_back(v);}}}
  std::vector<uint16_t> row(496*480,65535);
  for(int tp=0;tp<496;++tp)for(int k=0;k<4;++k)for(int rx=0;rx<10;++rx)for(int ry=0;ry<12;++ry){int x=(k<2?1:-1)*(20+rx),y=(k%2==0?1:-1)*(24+ry),best=65535;if(index[tp]>=0)best=d[state(x,y,index[tp])];for(auto a:incoming[tp])if(index[a.from]>=0)best=std::min(best,int(d[state(x,y,index[a.from])])+a.delay);row[tp*480+k*120+rx*12+ry]=uint16_t(std::min(best,65535));}
  out.write(reinterpret_cast<char*>(row.data()),row.size()*2);if(si%8==0)std::cerr<<"source="<<si<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }
 if(!out)throw std::runtime_error("Anchor output failure");std::cerr<<"complete bytes="<<out.tellp()<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
