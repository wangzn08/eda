// Tight directional periodic distance labels, computed only from architecture.
#include "routing_search.hpp"
#include <fstream>
#include <queue>
#include <iostream>
#include <ctime>
struct Edge{int from,to,dx,dy,cost;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("Expected raw output");std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::array<uint16_t,160>ports;unsigned inputs=0;for(unsigned i=0;i<std::size(archdata::NETS);++i){auto n=archdata::NETS[i];if(index[n.to]>=0)throw std::runtime_error("Duplicate input");index[n.to]=inputs;ports[inputs++]=n.to;netout[n.from]=i;}if(inputs!=160)throw std::runtime_error("Expected160 inputs");
 std::vector<Edge>edges;std::array<std::vector<unsigned>,160>incoming;std::array<std::vector<std::pair<unsigned,int>>,496>terminal;
 for(unsigned p=0;p<496;++p)if(index[p]>=0)terminal[p].push_back({unsigned(index[p]),0});
 for(auto a:archdata::ARCS)if(index[a.from]>=0){terminal[a.to].push_back({unsigned(index[a.from]),12*int(a.delay)});if(netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];incoming[index[n.to]].push_back(edges.size());edges.push_back({index[a.from],index[n.to],v.x,v.y,12*int(a.delay+n.delay)});}}
 constexpr int inf=1000000000;const int ax[4]={150,150,-150,-150},ay[4]={127,-125,127,-125};std::vector<int32_t>table(size_t(2)*496*120*160*4,inf);auto start=std::clock();
 for(unsigned mode=0;mode<2;++mode)for(unsigned k=0;k<4;++k){std::array<int,160>h{};bool changed=false;for(unsigned round=0;round<160;++round){changed=false;for(auto e:edges){int v=h[e.from]+e.cost-ax[k]*e.dx-ay[k]*e.dy;if(v<h[e.to]){h[e.to]=v;changed=true;}}if(!changed)break;}if(changed)throw std::runtime_error("Negative cycle at tight potential");std::vector<int>weight;for(auto e:edges){int w=e.cost-ax[k]*e.dx-ay[k]*e.dy+h[e.from]-h[e.to];if(w<0)throw std::runtime_error("Negative reweighted edge");weight.push_back(w);}
  for(unsigned target=0;target<496;++target){if(terminal[target].empty())continue;std::vector<int>d(19200,inf);using Item=std::pair<int,int>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>>q;for(auto end:terminal[target]){unsigned u=end.first*120;int cost=end.second+h[end.first];if(cost<d[u]){d[u]=cost;q.push({cost,int(u)});}}
   while(!q.empty()){auto item=q.top();int g=item.first,u=item.second;q.pop();if(g!=d[u])continue;unsigned p=u/120,phase=u%120;int x=phase/12,y=phase%12;for(auto id:incoming[p]){auto e=edges[id];int ny=(y-e.dy)%12;if(ny<0)ny+=12;auto relax=[&](int dx,int extra){int nx=(x-dx)%10;if(nx<0)nx+=10;unsigned next=e.from*120+nx*12+ny;int value=g+weight[id]+extra;if(value<d[next]){d[next]=value;q.push({value,int(next)});}};relax(e.dx,0);if(mode && e.dx){int skip=e.dx>0?14:-14;relax(e.dx+skip,12*292-ax[k]*skip);}}}
   for(unsigned p=0;p<160;++p)for(unsigned phase=0;phase<120;++phase)table[(((size_t(mode)*496+target)*120+phase)*160+p)*4+k]=d[p*120+phase]>=inf?inf:d[p*120+phase]-h[p];if(target%64==0)std::cerr<<"mode="<<mode<<" slope="<<k<<" target="<<target<<" cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';
  }
 }
 std::ofstream f(argv[1],std::ios::binary);f.write("TIGHTRAW",8);f.write(archdata::HASH,64);uint32_t shape[]={1,2,496,120,160,4};f.write(reinterpret_cast<char*>(shape),sizeof(shape));f.write(reinterpret_cast<const char*>(ports.data()),320);f.write(reinterpret_cast<const char*>(ax),16);f.write(reinterpret_cast<const char*>(ay),16);f.write(reinterpret_cast<const char*>(table.data()),table.size()*4);if(!f)throw std::runtime_error("Table output failed");std::cerr<<"complete cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<" bytes="<<uint64_t(f.tellp())<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
