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
 constexpr int states=W*W*160;std::vector<uint16_t>d(states*4);std::vector<std::vector<uint32_t>> buckets(limit);
 std::ofstream out(argv[1],std::ios::binary);out.write("ANCHOR03",8);out.write(archdata::HASH,64);out.write(reinterpret_cast<char*>(ports.data()),320);
 auto begin=std::clock();
 std::array<int,4> cheap={-1,-1,-1,-1},cycle_cost={65535,65535,65535,65535};
 for(auto n:archdata::NETS){auto v=archdata::VECTORS[n.vector];int direction=v.x>0?0:v.x<0?1:v.y>0?2:3;for(auto a:incoming[n.from])if(a.from==n.to && a.delay+n.delay<cycle_cost[direction] && std::abs(v.x)+std::abs(v.y)>=10){cheap[direction]=index[n.to];cycle_cost[direction]=a.delay+n.delay;}}
 for(auto p:cheap)if(p<0)throw std::runtime_error("Missing minimum-cost cycle");
 for(int si=0;si<160;++si){std::vector<uint16_t>row(496*3316,65535);
  for(int k=0;k<4;++k){int cx=cheap[k<2?0:1],cy=cheap[k%2==0?2:3];std::fill(d.begin(),d.end(),65535);for(auto& b:buckets)b.clear();int flags=(si==cx?1:0)|(si==cy?2:0);auto initial=flags*states+state(0,0,si);d[initial]=0;buckets[0].push_back(initial);
   for(int cost=0;cost<limit;++cost)for(size_t at=0;at<buckets[cost].size();++at){auto u=buckets[cost][at];if(d[u]!=cost)continue;int local=u%states,mask=u/states,x=int(local/160)/W-R,y=int(local/160)%W-R;for(auto e:edges[local%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -R || nx>R || ny < -R || ny>R || value>=limit)continue;int next=mask|(e.to==cx?1:0)|(e.to==cy?2:0);auto v=next*states+state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value].push_back(v);}}}
   auto finish=[&](int x,int y,int tp,int required){int best=65535;for(int mask=0;mask<4;++mask)if((mask&required)==required){if(index[tp]>=0)best=std::min(best,int(d[mask*states+state(x,y,index[tp])]));for(auto a:incoming[tp])if(index[a.from]>=0)best=std::min(best,int(d[mask*states+state(x,y,index[a.from])])+a.delay);}return uint16_t(std::min(best,65535));};
   for(int tp=0;tp<496;++tp){
    // x extension: 20 signed residues times all 71 local y values.
    for(int rx=0;rx<10;++rx)for(int y=-35;y<=35;++y)if((y>=0)==(k%2==0)){int x=(k<2?1:-1)*(20+rx);row[tp*3316+(k<2?0:10)*71+rx*71+y+35]=finish(x,y,tp,1);}
    // y extension: 24 signed residues times all 59 local x values.
    for(int ry=0;ry<12;++ry)for(int x=-29;x<=29;++x)if((x>=0)==(k<2)){int y=(k%2==0?1:-1)*(24+ry);row[tp*3316+1420+(k%2==0?0:12)*59+ry*59+x+29]=finish(x,y,tp,2);}
    for(int rx=0;rx<10;++rx)for(int ry=0;ry<12;++ry){int x=(k<2?1:-1)*(20+rx),y=(k%2==0?1:-1)*(24+ry);row[tp*3316+2836+k*120+rx*12+ry]=finish(x,y,tp,3);}
   }
  }
  out.write(reinterpret_cast<char*>(row.data()),row.size()*2);if(si%4==0)std::cerr<<"source="<<si<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }
 if(!out)throw std::runtime_error("Anchor output failure");std::cerr<<"complete bytes="<<out.tellp()<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
