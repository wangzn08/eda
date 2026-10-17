// Phase-aware min-plus boundary penalties. All supervision is architecture-only.
// Compare bounded Bellman updates on real geometry with periodic ideal updates,
// initialized by four finite ideal landmark distance functions.
#include "core_template_model.hpp"
#include <fstream>
#include <ctime>
struct PhasePotentialEdge { uint16_t core,vector,net;int32_t cost,dx,dy; };
int phase_mod(int value,int period){int r=value%period;return r<0?r+period:r;}
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Core asset and raw field output required");
 Graph graph;CoreTemplateModel model(argv[1]);std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::array<uint16_t,160>ports{};unsigned count=0;
 for(unsigned i=0;i<std::size(archdata::NETS);++i){auto n=archdata::NETS[i];ports[count]=n.to;index[n.to]=count++;netout[n.from]=i;}if(count!=160)throw std::runtime_error("Core count");
 std::array<std::vector<PhasePotentialEdge>,160>forward,reverse;
 for(auto a:archdata::ARCS)if(index[a.from]>=0&&netout[a.to]>=0){int ni=netout[a.to];auto n=archdata::NETS[ni];auto v=archdata::VECTORS[n.vector];unsigned u=index[a.from],t=index[n.to];forward[u].push_back({uint16_t(t),uint16_t(n.vector),uint16_t(ni),a.delay+n.delay,v.x,v.y});reverse[t].push_back({uint16_t(u),uint16_t(n.vector),uint16_t(ni),a.delay+n.delay,-v.x,-v.y});}
 std::array<int,120>xgap{};std::array<int,550>ygap{};for(auto l:archdata::LINES){if(l.vertical)for(int x=l.site+1;x<120;++x)xgap[x]+=l.delay;else for(int y=l.site+1;y<550;++y)ygap[y]+=l.delay;}
 constexpr int large=100000000;size_t n=std::size(archdata::SITES)*160;std::vector<std::array<int32_t,4>>previous(n),next(n);std::vector<std::array<int32_t,4>>ideal(160*120),ideal_next(ideal.size());
 const int landmark[4]={0,53,106,159},goalx[4]={0,3,6,9},goaly[4]={0,4,8,0},wx[4]={750,750,-750,-750},sx[4]={1,1,-1,-1},sy[4]={1,-1,1,-1};
 std::ofstream f(argv[2],std::ios::binary);f.write("PHIPH001",8);f.write(archdata::HASH,64);uint32_t shape[6]={4,2,2,uint32_t(std::size(archdata::SITES)),160,4};f.write(reinterpret_cast<char*>(shape),24);auto begin=std::clock();
 for(unsigned proto=0;proto<4;++proto)for(unsigned mode=0;mode<2;++mode){auto&edges=mode?reverse:forward;const int wy[4]={mode?625:635,mode?-635:-625,mode?625:635,mode?-635:-625};
  for(unsigned p=0;p<160;++p)for(int x=0;x<10;++x)for(int y=0;y<12;++y)for(unsigned k=0;k<4;++k){int dx=sx[k]*(20+phase_mod(sx[k]*(goalx[proto]-x),10)),dy=sy[k]*(24+phase_mod(sy[k]*(goaly[proto]-y),12));Distance distance=mode?model.finite_nominal(ports[landmark[proto]],ports[p],-dx,-dy):model.finite_nominal(ports[p],ports[landmark[proto]],dx,dy);if(distance>=INF)throw std::runtime_error("Unreachable ideal landmark");ideal[(size_t(p)*10+x)*12+y][k]=int(distance)*60-wx[k]*dx-wy[k]*dy;}
  for(Node site=0;site<std::size(archdata::SITES);++site){auto a=archdata::SITES[site];for(unsigned p=0;p<160;++p)previous[size_t(site)*160+p]=ideal[(size_t(p)*10+a.x%10)*12+a.y%12];}
  for(unsigned depth=1;depth<=4;++depth){for(unsigned p=0;p<160;++p)for(int x=0;x<10;++x)for(int y=0;y<12;++y){auto&out=ideal_next[(size_t(p)*10+x)*12+y];out.fill(large);for(auto e:edges[p]){auto&tail=ideal[(size_t(e.core)*10+phase_mod(x+e.dx,10))*12+phase_mod(y+e.dy,12)];for(unsigned k=0;k<4;++k)out[k]=std::min(out[k],e.cost*60-wx[k]*e.dx-wy[k]*e.dy+tail[k]);}}
   for(Node site=0;site<std::size(archdata::SITES);++site){auto a=archdata::SITES[site];for(unsigned p=0;p<160;++p){auto&out=next[size_t(site)*160+p];out.fill(large);for(auto e:edges[p]){Move m=mode?graph.net_move(site,e.net,true):graph.forward_vector_move(site,e.vector);if(m.site==NONE)continue;auto b=archdata::SITES[m.site];auto&tail=previous[size_t(m.site)*160+e.core];int dx=b.x-a.x,dy=b.y-a.y,gx=xgap[b.x]-xgap[a.x],gy=ygap[b.y]-ygap[a.y];for(unsigned k=0;k<4;++k){if(tail[k]>=large)continue;int value=(e.cost+int(m.delay))*60-wx[k]*dx-wy[k]*dy-60*(sx[k]*gx+sy[k]*gy)+tail[k];out[k]=std::min(out[k],value);}}}}
   previous.swap(next);ideal.swap(ideal_next);
   if(depth==2||depth==4){std::vector<int16_t>row(160*4);uint64_t negative=0,clipped=0;for(Node site=0;site<std::size(archdata::SITES);++site){auto a=archdata::SITES[site];for(unsigned p=0;p<160;++p)for(unsigned k=0;k<4;++k){int value=previous[size_t(site)*160+p][k]>=large?32767:(previous[size_t(site)*160+p][k]-ideal[(size_t(p)*10+a.x%10)*12+a.y%12][k])/5;if(value<0)++negative;if(value<-32768||value>32767)++clipped;row[p*4+k]=int16_t(std::clamp(value,-32768,32767));}f.write(reinterpret_cast<char*>(row.data()),row.size()*2);}std::cerr<<"proto="<<proto<<" mode="<<mode<<" depth="<<depth<<" negative="<<negative<<" clipped="<<clipped<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';}
  }
 }
 if(!f)throw std::runtime_error("Potential field output");std::cerr<<"bytes="<<uint64_t(f.tellp())<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
