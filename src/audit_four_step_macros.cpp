// Architecture-only four-step min-plus composition feasibility audit.
// Geometry is ideal here; this is not a prediction/submission executable.
#include "routing_search.hpp"
#include <unordered_map>
#include <fstream>
#include <iostream>
#include <ctime>
struct Edge{int target,dx,dy,cost,net;};
struct Value{int cost;uint32_t path;};
uint32_t encode(int core,int x,int y){if(std::abs(x)>64||std::abs(y)>64)throw std::runtime_error("Macro span");return ((x+64)*129+y+64)*160+core;}
int mod(int x,int n){int r=x%n;return r<0?r+n:r;}
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("Macro raw output required");
 std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);unsigned count=0;
 for(unsigned i=0;i<std::size(archdata::NETS);++i){auto n=archdata::NETS[i];index[n.to]=count++;netout[n.from]=i;}if(count!=160)throw std::runtime_error("Core count");
 std::array<std::vector<Edge>,160>edges;for(auto a:archdata::ARCS)if(index[a.from]>=0 && netout[a.to]>=0){int ni=netout[a.to];auto n=archdata::NETS[ni];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay,ni});}
 std::ofstream f(argv[1],std::ios::binary);f.write("MACROID1",8);f.write(archdata::HASH,64);uint32_t bytes=16;f.write(reinterpret_cast<char*>(&bytes),4);uint64_t states=0,groups=0,unique_witnesses=0;auto begin=std::clock();
 for(unsigned source=0;source<160;++source){std::unordered_map<uint32_t,Value>current,next;current.emplace(encode(source,0,0),Value{0,0});
  for(unsigned depth=0;depth<4;++depth){next.clear();next.reserve(current.size()*3);for(auto [key,value]:current){int core=key%160,x=int(key/160)/129-64,y=int(key/160)%129-64;for(auto e:edges[core]){auto k=encode(e.target,x+e.dx,y+e.dy);Value v{value.cost+e.cost,value.path|(uint32_t(e.net)<<(8*depth))};auto p=next.find(k);if(p==next.end())next.emplace(k,v);else if(v.cost<p->second.cost || (v.cost==p->second.cost && v.path<p->second.path))p->second=v;}}current.swap(next);}
  std::unordered_map<uint32_t,std::array<std::pair<int64_t,uint32_t>,4>>quotient;
  for(auto [key,value]:current){int core=key%160,x=int(key/160)/129-64,y=int(key/160)%129-64;uint16_t s=source,t=core;int16_t dx=x,dy=y;f.write(reinterpret_cast<char*>(&s),2);f.write(reinterpret_cast<char*>(&t),2);f.write(reinterpret_cast<char*>(&dx),2);f.write(reinterpret_cast<char*>(&dy),2);f.write(reinterpret_cast<char*>(&value.cost),4);f.write(reinterpret_cast<char*>(&value.path),4);
   auto k=(core*10+mod(x,10))*12+mod(y,12);auto [p,fresh]=quotient.try_emplace(k);if(fresh)for(auto&v:p->second)v={INT64_MAX,0};unsigned q=0;for(int sx:{-1,1})for(int sy:{-1,1}){int64_t normalized=int64_t(value.cost)*60-int64_t(x)*sx*750-int64_t(y)*(sy>0?635:-625);auto&v=p->second[q++];if(normalized<v.first || (normalized==v.first&&value.path<v.second))v={normalized,value.path};}}
  uint64_t witnesses=0;for(auto [key,v]:quotient){std::array<uint32_t,4>w;for(unsigned i=0;i<4;++i)w[i]=v[i].second;std::sort(w.begin(),w.end());witnesses+=std::unique(w.begin(),w.end())-w.begin();}
  states+=current.size();groups+=quotient.size();unique_witnesses+=witnesses;std::cerr<<"core="<<source<<" states="<<current.size()<<" groups="<<quotient.size()<<" witnesses="<<witnesses<<'\n';
 }
 if(!f)throw std::runtime_error("Macro output write");std::cout<<"{\"states\":"<<states<<",\"phase_groups\":"<<groups<<",\"quadrant_witnesses\":"<<unique_witnesses<<",\"cpu_seconds\":"<<double(std::clock()-begin)/CLOCKS_PER_SEC<<",\"scope\":\"Ideal geometry macro composition only, no validation or runtime claim\"}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
