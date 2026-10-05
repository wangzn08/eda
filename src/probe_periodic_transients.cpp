// Architecture-only recurrence probe; finite nominal graph, not physical-path certificate.
#include "architecture_data.hpp"
#include <array>
#include <algorithm>
#include <vector>
#include <fstream>
#include <iostream>
#include <ctime>
struct E{int to,dx,dy,cost;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("Expected output CSV");std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::vector<int>ports;
 for(unsigned i=0;i<std::size(archdata::NETS);++i){auto n=archdata::NETS[i];index[n.to]=ports.size();ports.push_back(n.to);netout[n.from]=i;}
 std::vector<std::vector<E>>edges(160);for(auto a:archdata::ARCS)if(index[a.from]>=0 && netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay});}
 constexpr int R=112,W=225,limit=4096;auto state=[](int x,int y,int p){return ((x+R)*W+y+R)*160+p;};std::vector<uint16_t>d(W*W*160);std::vector<std::vector<uint32_t>>buckets(limit);std::ofstream out(argv[1]);out<<"source,target,dx,dy,delay\n";auto begin=std::clock();
 for(int si:{0,80,159}){std::fill(d.begin(),d.end(),65535);for(auto& b:buckets)b.clear();d[state(0,0,si)]=0;buckets[0].push_back(state(0,0,si));
  for(int cost=0;cost<limit;++cost)for(size_t j=0;j<buckets[cost].size();++j){auto u=buckets[cost][j];if(d[u]!=cost)continue;int x=int(u/160)/W-R,y=int(u/160)%W-R;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -R || nx>R || ny < -R || ny>R || value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value].push_back(v);}}}
  for(int ti=0;ti<160;++ti)for(int x:{-29,-20,-10,0,10,20,29})for(int y=-83;y<=83;++y)out<<si<<','<<ti<<','<<x<<','<<y<<','<<d[state(x,y,ti)]<<'\n';out.flush();std::cerr<<"source="<<si<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';}
 if(!out)throw std::runtime_error("Output failed");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
