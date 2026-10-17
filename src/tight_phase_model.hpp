#pragma once
#include "core_template_model.hpp"
#ifdef __aarch64__
#include <arm_neon.h>
#endif
class TightPhaseModel {
 std::array<int,496>index,netout;std::array<int,550>block_at;std::array<Distance,120>xgap{};std::array<Distance,550>ygap{};std::vector<int32_t>cells;std::unique_ptr<CoreTemplateModel>finite;int hub=0;bool required=false;int threshold_x=30,threshold_y=36;
 struct Entry{uint16_t vector,port;uint32_t cost;};std::array<std::vector<Entry>,496>entries;
 Distance nominal(int source,int target,int dx,int dy,unsigned mode,bool local=true)const{
  if(local && finite && mode==0 && std::abs(dx)<=29 && std::abs(dy)<=35)return finite->finite_nominal(source,target,dx,dy);
  if(required)mode=(std::abs(dx)>=threshold_x?1:0)|(std::abs(dy)>=threshold_y?2:0);
  int rx=(-dx)%10,ry=(-dy)%12;if(rx<0)rx+=10;if(ry<0)ry+=12;const int32_t*c=cells.data()+((((size_t(mode)*496+target)*120+rx*12+ry)*160+index[source])*4);if(c[0]>=1000000000)return INF;
  int gx=150*dx,up=127*dy,down=-125*dy;int best;
#ifdef __aarch64__
  int32_t geo[4]={gx+up,gx+down,-gx+up,-gx+down};best=vmaxvq_s32(vaddq_s32(vld1q_s32(c),vld1q_s32(geo)));
#else
  best=std::max(std::max(c[0]+gx+up,c[1]+gx+down),std::max(c[2]-gx+up,c[3]-gx+down));
#endif
#ifdef TIGHT_QUADRANT_ONLY
  if(required){unsigned k=(dx<0?2:0)|(dy<0?1:0);best=c[k]+(dx<0?-gx:gx)+(dy<0?down:up);}
#endif
  return Distance(std::max(0,(best+11)/12));
 }
public:
 TightPhaseModel(const std::string&path,const std::string&near_path=""){
  std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated tight model");};char magic[8],hash[64];uint32_t shape[6];std::array<uint16_t,160>ports;int ax[4],ay[4];read(magic,8);read(hash,64);read(shape,24);read(ports.data(),320);read(ax,16);read(ay,16);if((std::string(magic,8)!="TIGHTRAW" && std::string(magic,8)!="TIGHTXZ1" && std::string(magic,8)!="TIGHTREQ") || std::string(hash,64)!=archdata::HASH || shape[0]!=1 || (shape[1]!=2 && shape[1]!=4) || shape[2]!=496 || shape[3]!=120 || shape[4]!=160 || shape[5]!=4)throw std::runtime_error("Tight asset header mismatch");const int expectedx[4]={150,150,-150,-150},expectedy[4]={127,-125,127,-125};for(unsigned i=0;i<4;++i)if(ax[i]!=expectedx[i] || ay[i]!=expectedy[i])throw std::runtime_error("Tight slopes mismatch");index.fill(-1);netout.fill(-1);for(unsigned i=0;i<160;++i){if(ports[i]>=496 || index[ports[i]]>=0)throw std::runtime_error("Tight input mismatch");index[ports[i]]=i;}required=std::string(magic,8)=="TIGHTREQ";if(required!=(shape[1]==4))throw std::runtime_error("Required shape mismatch");cells.resize(size_t(shape[1])*496*120*160*4);
  if(std::string(magic,8)=="TIGHTRAW" || required)read(cells.data(),cells.size()*4);else{uint64_t decoded;read(&decoded,8);if(decoded!=cells.size()*4)throw std::runtime_error("Tight decoded size mismatch");std::vector<unsigned char>compressed((std::istreambuf_iterator<char>(f)),{});if(compressed.empty() || compressed.size()>100000000 || !decode_xz_exact(compressed.data(),compressed.size(),reinterpret_cast<unsigned char*>(cells.data()),decoded))throw std::runtime_error("Invalid tight compressed data");}
  for(unsigned i=0;i<std::size(archdata::NETS);++i)netout[archdata::NETS[i].from]=i;int hub_port=-1;for(auto n:archdata::NETS){auto v=archdata::VECTORS[n.vector];if(v.x==10 && hub_port<0)hub_port=n.to;}if(hub_port<0)throw std::runtime_error("No horizontal hub");hub=hub_port;
  for(auto a:archdata::ARCS)if(netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];entries[a.from].push_back({uint16_t(n.vector),uint16_t(n.to),uint32_t(a.delay+n.delay)});}
  block_at.fill(-1);for(unsigned i=0;i<std::size(archdata::BLOCKS);++i){auto b=archdata::BLOCKS[i];for(int y=b.lower;y<=b.upper;++y)block_at[y]=i;}for(auto l:archdata::LINES){if(l.vertical)for(int x=l.site+1;x<120;++x)xgap[x]+=l.delay;else for(int y=l.site+1;y<550;++y)ygap[y]+=l.delay;}
  if(!near_path.empty()){finite=std::make_unique<CoreTemplateModel>(near_path);finite->enable_finite_hints();if(CORE_CORE_PHASE_MAJOR)finite->enable_core_layout();}
 }
 void thresholds(int x,int y){if(x<30 || y<36)throw std::runtime_error("Required thresholds overlap the finite window");threshold_x=x;threshold_y=y;}
 Distance predict(const Graph&graph,Node source,Node target,unsigned mode)const{
  if(required && mode==1)throw std::runtime_error("Required model has no relaxed-wall table");if(source==target)return 0;Node site=source/496;int sp=source%496,tp=target%496;auto b=archdata::SITES[target/496];Distance best=INF;std::array<Distance,2>seconds{};std::array<bool,2>ready{};
  auto bound=[&](Node s,int p){auto a=archdata::SITES[s];int dx=b.x-a.x,dy=b.y-a.y;bool cross=std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89;Distance value=nominal(p,tp,dx,dy,mode==1 && cross?1:0);if(mode==2 && cross){const archdata::Block*block=nullptr;if(block_at[a.y]>=0){auto&z=archdata::BLOCKS[block_at[a.y]];if(b.y>=z.lower && b.y<=z.upper)block=&z;}
   if(block){value=INF;auto corridor=[&](int cy,unsigned side){if(!ready[side]){seconds[side]=nominal(hub,tp,b.x-82,b.y-cy,0);ready[side]=true;}Distance extra=Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[cy])))+Distance(std::llabs(int64_t(ygap[b.y])-int64_t(ygap[cy])))-Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));return nominal(p,hub,82-a.x,cy-a.y,0)+seconds[side]+extra;};if(block->lower>0)value=std::min(value,corridor(block->lower-1,0));if(block->upper+1<550)value=std::min(value,corridor(block->upper+1,1));}
   value=std::min(value,nominal(p,tp,dx+(dx>0?-14:14),dy,0)+292);
  }return value+Distance(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x])))+Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));};
  auto add=[&](Node s,int p,Distance cost){best=std::min(best,cost+bound(s,p));};if(site==target/496)for(auto e:graph.local_out(sp))if(e.port==tp)best=std::min(best,Distance(e.delay));if(index[sp]>=0)add(site,sp,0);else if(netout[sp]>=0){auto n=archdata::NETS[netout[sp]];auto m=graph.forward_vector_move(site,n.vector);if(m.site!=NONE)add(m.site,n.to,m.delay+n.delay);}else for(auto e:entries[sp]){auto m=graph.forward_vector_move(site,e.vector);if(m.site!=NONE)add(m.site,e.port,Distance(e.cost)+m.delay);}return best;
 }
};
