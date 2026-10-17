// Full near-x late response curves from architecture-only finite ideal graph.
#include "core_template_model.hpp"
#include <fstream>
#include <iostream>
#include <ctime>
struct CurveEdge{int to,dx,dy,cost;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("raw output required");
 std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::array<uint16_t,160>ports;unsigned count=0;
 for(unsigned k=0;k<std::size(archdata::NETS);++k){auto n=archdata::NETS[k];index[n.to]=count;ports[count++]=n.to;netout[n.from]=k;}if(count!=160)throw std::runtime_error("core count");
 std::array<std::vector<CurveEdge>,160>edges;for(auto a:archdata::ARCS)if(index[a.from]>=0&&netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay});}
 constexpr int RX=156,RY=624,WX=313,WY=1249,limit=9000;auto state=[](int x,int y,int p){return ((x+RX)*WY+y+RY)*160+p;};
 std::vector<uint16_t>d(size_t(WX)*WY*160);std::vector<std::vector<uint32_t>>buckets(limit);std::ofstream out(argv[1],std::ios::binary);if(!out)throw std::runtime_error("output");
 out.write("CURVRAW2",8);out.write(archdata::HASH,64);out.write(reinterpret_cast<char*>(ports.data()),320);uint32_t shape[6]={160,160,59,24,40,2};out.write(reinterpret_cast<char*>(shape),24);std::array<uint32_t,160>sources;for(unsigned i=0;i<160;++i)sources[i]=i;out.write(reinterpret_cast<char*>(sources.data()),640);auto begin=std::clock();
 for(auto si:sources){std::fill(d.begin(),d.end(),65535);for(auto&b:buckets)b.clear();d[state(0,0,si)]=0;buckets[0].push_back(state(0,0,si));
  for(int cost=0;cost<limit;++cost)for(size_t j=0;j<buckets[cost].size();++j){auto u=buckets[cost][j];if(d[u]!=cost)continue;int x=int(u/160)/WY-RX,y=int(u/160)%WY-RY;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -RX||nx>RX||ny < -RY||ny>RY||value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value].push_back(v);}}}
  for(unsigned ti=0;ti<160;++ti)for(int x=-29;x<=29;++x)for(int sign:{-1,1})for(int r=0;r<12;++r){for(int q=8;q<48;++q){int y=sign*(r+12*q);int truth=d[state(x,y,ti)];if(truth==65535)throw std::runtime_error("unreachable curve");int64_t delta=truth-q*(sign>0?127:125);if(delta < -32768||delta>32767)throw std::runtime_error("curve overflow");int16_t v=delta;out.write(reinterpret_cast<char*>(&v),2);}}
  std::cerr<<"source="<<si<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }
 if(!out)throw std::runtime_error("write");std::cerr<<"bytes="<<uint64_t(out.tellp())<<'\n';
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
