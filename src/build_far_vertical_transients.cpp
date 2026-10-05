// Independent farther-distance recurrence probe at72..95; no request labels.
#include "architecture_data.hpp"
#include <array>
#include <algorithm>
#include <vector>
#include <fstream>
#include <iostream>
#include <ctime>
struct E{int to,dx,dy,cost;};
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Expected original dense asset and output residual asset");std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::vector<int>ports;
 for(unsigned i=0;i<std::size(archdata::NETS);++i){auto n=archdata::NETS[i];index[n.to]=ports.size();ports.push_back(n.to);netout[n.from]=i;}
 std::vector<std::vector<E>>edges(160);for(auto a:archdata::ARCS)if(index[a.from]>=0 && netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay});}
 constexpr int R=112,W=225,limit=4096;auto state=[](int x,int y,int p){return ((x+R)*W+y+R)*160+p;};std::vector<uint16_t>d(W*W*160);std::vector<std::vector<uint32_t>>buckets(limit);std::ifstream old(argv[1],std::ios::binary);char oldmagic[8],hash[64];std::array<uint16_t,160>oldports;old.read(oldmagic,8);old.read(hash,64);old.read(reinterpret_cast<char*>(oldports.data()),320);if(std::string(oldmagic,8)!="ANCHOR02" || std::string(hash,64)!=archdata::HASH)throw std::runtime_error("Original asset mismatch");for(unsigned i=0;i<160;++i)if(oldports[i]!=ports[i])throw std::runtime_error("Port order mismatch");
 std::vector<uint16_t>oldrow(496*59*71);std::ofstream out(argv[2],std::ios::binary);out.write("TRANSVF1",8);out.write(archdata::HASH,64);out.write(reinterpret_cast<char*>(oldports.data()),320);auto begin=std::clock();
 for(int si=0;si<160;++si){std::fill(d.begin(),d.end(),65535);for(auto& b:buckets)b.clear();d[state(0,0,si)]=0;buckets[0].push_back(state(0,0,si));
  for(int cost=0;cost<limit;++cost)for(size_t j=0;j<buckets[cost].size();++j){auto u=buckets[cost][j];if(d[u]!=cost)continue;int x=int(u/160)/W-R,y=int(u/160)%W-R;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -R || nx>R || ny < -R || ny>R || value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value].push_back(v);}}}
  old.read(reinterpret_cast<char*>(oldrow.data()),oldrow.size()*2);if(!old)throw std::runtime_error("Truncated original row");std::vector<int16_t>row;row.reserve(160*59*48);
  for(int ti=0;ti<160;++ti)for(int x=-29;x<=29;++x)for(int sign:{-1,1})for(int band:{72,84})for(int residue=0;residue<12;++residue){int anchor=sign*(24+residue);int base=oldrow[(ports[ti]*59+x+29)*71+anchor+35];int value=d[state(x,sign*(band+residue),ti)];if(base==65535 || value==65535)throw std::runtime_error("Unreachable transient entry");int delta=value-base-((band-24)/12)*(sign>0?127:125);if(delta < -32768 || delta>32767)throw std::runtime_error("Transient residual overflow");row.push_back(int16_t(delta));}
  out.write(reinterpret_cast<char*>(row.data()),row.size()*2);out.flush();std::cerr<<"source="<<si<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';}
 if(!out)throw std::runtime_error("Output failed");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
