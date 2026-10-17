// Full near-x late response curves from architecture-only finite ideal graph.
#include "core_template_model.hpp"
#include <fstream>
#include <iostream>
#include <ctime>
struct CurveEdge{int to,dx,dy,cost,net;};
int main(int argc,char**argv){try{
 if(argc!=2&&argc!=3)throw std::runtime_error("raw output [--all] required");bool all=argc==3&&std::string(argv[2])=="--all";if(argc==3&&!all)throw std::runtime_error("Unknown generation mode");
 std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::array<uint16_t,160>ports;unsigned count=0;
 for(unsigned k=0;k<std::size(archdata::NETS);++k){auto n=archdata::NETS[k];index[n.to]=count;ports[count++]=n.to;netout[n.from]=k;}if(count!=160)throw std::runtime_error("core count");
 std::array<std::vector<CurveEdge>,160>edges;for(auto a:archdata::ARCS)if(index[a.from]>=0&&netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay,netout[a.to]});}
 constexpr int RX=156,RY=624,WX=313,WY=1249,limit=9000;auto state=[](int x,int y,int p){return ((x+RX)*WY+y+RY)*160+p;};
 std::vector<uint16_t>d(size_t(WX)*WY*160);std::vector<uint8_t>first(d.size(),255);std::vector<std::vector<uint32_t>>buckets(limit);std::ofstream out(argv[1],std::ios::binary);if(!out)throw std::runtime_error("output");
 out.write("ACTCURV1",8);out.write(archdata::HASH,64);out.write(reinterpret_cast<char*>(ports.data()),320);std::vector<int32_t>xs;for(int x=-29;x<=29;++x)xs.push_back(x);for(int sign:{-1,1})for(int q:{1,4,8})for(int r=0;r<10;++r)xs.push_back(sign*(20+q*10+r));std::vector<uint32_t>sources;if(all)for(unsigned i=0;i<160;++i)sources.push_back(i);else sources={0,53,106,159};uint32_t shape[6]={uint32_t(sources.size()),160,uint32_t(xs.size()),24,48,1};out.write(reinterpret_cast<char*>(shape),24);out.write(reinterpret_cast<char*>(sources.data()),sources.size()*4);out.write(reinterpret_cast<char*>(xs.data()),xs.size()*4);auto begin=std::clock();
 for(auto si:sources){std::fill(d.begin(),d.end(),65535);std::fill(first.begin(),first.end(),255);for(auto&b:buckets)b.clear();d[state(0,0,si)]=0;buckets[0].push_back(state(0,0,si));
  for(int cost=0;cost<limit;++cost)for(size_t j=0;j<buckets[cost].size();++j){auto u=buckets[cost][j];if(d[u]!=cost)continue;int x=int(u/160)/WY-RX,y=int(u/160)%WY-RY;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -RX||nx>RX||ny < -RY||ny>RY||value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;first[v]=u==uint32_t(state(0,0,si))?uint8_t(e.net):first[u];buckets[value].push_back(v);}}}
  for(unsigned ti=0;ti<160;++ti)for(int x:xs)for(int sign:{-1,1})for(int r=0;r<12;++r)for(int q=0;q<48;++q){int y=sign*(r+12*q);auto u=state(x,y,ti);if(d[u]==65535)throw std::runtime_error("unreachable action curve");uint8_t action=first[u];if(action==255 && (x||y||ti!=si))throw std::runtime_error("missing first action");out.write(reinterpret_cast<char*>(&action),1);}
  std::cerr<<"source="<<si<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }
 if(!out)throw std::runtime_error("write");std::cerr<<"bytes="<<uint64_t(out.tellp())<<'\n';
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
