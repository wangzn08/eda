// Independent nominal Dijkstra vs additive directional transient model.
#include "core_template_model.hpp"
#include <array>
#include <vector>
#include <fstream>
#include <iostream>
#include <ctime>
struct ProbeEdge {int to,dx,dy,cost;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("Expected output csv");
 CoreTemplateModel model("out/architecture-benchmark/core-template-xz6.bin",false,0,0,"out/architecture-benchmark/vertical-transients-xz.bin",UINT_MAX,"out/architecture-benchmark/horizontal-transients.bin","out/architecture-benchmark/vertical-distant-delta-xz6.bin");
 std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::vector<int>ports;
 for(unsigned i=0;i<std::size(archdata::NETS);++i){auto n=archdata::NETS[i];index[n.to]=ports.size();ports.push_back(n.to);netout[n.from]=i;}
 std::vector<std::vector<ProbeEdge>>edges(160);
 for(auto a:archdata::ARCS)if(index[a.from]>=0 && netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay});}
 constexpr int R=144,W=289,limit=5000;auto state=[](int x,int y,int p){return ((x+R)*W+y+R)*160+p;};
 std::vector<uint16_t>d(W*W*160);std::vector<std::vector<uint32_t>>buckets(limit);
 std::ofstream out(argv[1],std::ios::binary);if(!out)throw std::runtime_error("Output open failed");out.write("TRMRAW01",8);out.write(archdata::HASH,64);for(int port:ports){uint16_t p=port;out.write(reinterpret_cast<char*>(&p),2);}
 uint32_t shape[2]={3,3};int32_t qxs[3]={1,2,5},qys[3]={1,2,6};uint64_t bytes=221184000;out.write(reinterpret_cast<char*>(shape),8);out.write(reinterpret_cast<char*>(qxs),12);out.write(reinterpret_cast<char*>(qys),12);out.write(reinterpret_cast<char*>(&bytes),8);auto begin=std::clock();
 for(int si=0;si<160;++si){
  std::fill(d.begin(),d.end(),65535);for(auto& b:buckets)b.clear();d[state(0,0,si)]=0;buckets[0].push_back(state(0,0,si));
  for(int cost=0;cost<limit;++cost)for(size_t j=0;j<buckets[cost].size();++j){auto u=buckets[cost][j];if(d[u]!=cost)continue;int x=int(u/160)/W-R,y=int(u/160)%W-R;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -R || nx>R || ny < -R || ny>R || value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value].push_back(v);}}}
  for(int ti=0;ti<160;++ti)for(int sx:{-1,1})for(int sy:{-1,1})for(int rx=0;rx<10;++rx)for(int ry=0;ry<12;++ry){
   for(int qx:qxs)for(int qy:qys){int dx=sx*(20+qx*10+rx),dy=sy*(24+qy*12+ry);int truth=d[state(dx,dy,ti)];if(truth==65535)throw std::runtime_error("Unreachable joint anchor");int64_t delta=truth-model.direct_nominal_probe(ports[si],ports[ti],dx,dy);if(delta < -32768 || delta>32767)throw std::runtime_error("Joint delta overflow");int16_t v=delta;out.write(reinterpret_cast<char*>(&v),2);}
  }
  std::cerr<<"source="<<si<<" complete cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<"\n";
 }
 if(!out)throw std::runtime_error("Output write failed");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
