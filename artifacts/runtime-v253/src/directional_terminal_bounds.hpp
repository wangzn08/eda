#pragma once
// Lagrangian relaxation of the displacement constraints. Every path obeys
// cost >= lambda*displacement + the reduced-cost quotient shortest distance.
// The four certified duals also respect the integer10-unit x interpolation.
#include "routing_search.hpp"
class DirectionalTerminalBounds{
 struct __attribute__((packed)) Entry{int16_t reduced;uint8_t ordinal;};
 std::vector<Entry>order;std::array<uint32_t,4*160*496>starts{};std::array<unsigned,496>counts{};
 static constexpr int wx[4]={150,150,-150,-150},wy[4]={127,-125,127,-125};
public:
 static unsigned direction(int dx,int dy){return (dx<0)*2+(dy<0);}
 static int geometry(unsigned d,int dx,int dy){return wx[d]*dx+wy[d]*dy;}
 static int ceil12(int value){return value>=0?(value+11)/12:value/12;}
 template<class Terminal>
 explicit DirectionalTerminalBounds(const Terminal&terminal){
  std::array<int,496>core,out;core.fill(-1);out.fill(-1);for(unsigned i=0;i<160;++i){core[archdata::NETS[i].to]=i;out[archdata::NETS[i].from]=i;}for(unsigned t=0;t<496;++t)counts[t]=terminal[t].size();
  constexpr int inf=100000000;std::vector<int32_t>dist(160*160);
  for(unsigned d=0;d<4;++d){std::fill(dist.begin(),dist.end(),inf);for(unsigned i=0;i<160;++i)dist[i*160+i]=0;for(auto a:archdata::ARCS)if(core[a.from]>=0&&out[a.to]>=0){auto n=archdata::NETS[out[a.to]];auto v=archdata::VECTORS[n.vector];int value=(a.delay+n.delay)*12-wx[d]*v.x-wy[d]*v.y;auto&slot=dist[core[a.from]*160+core[n.to]];slot=std::min(slot,value);}
   for(unsigned k=0;k<160;++k)for(unsigned s=0;s<160;++s){int to=dist[s*160+k];if(to==inf)continue;for(unsigned t=0;t<160;++t)if(dist[k*160+t]!=inf)dist[s*160+t]=std::min(dist[s*160+t],to+dist[k*160+t]);}
   for(unsigned s=0;s<160;++s)if(dist[s*160+s]<0)throw std::runtime_error("Directional dual has a negative cycle");
   for(unsigned s=0;s<160;++s)for(unsigned t=0;t<496;++t){starts[(d*160+s)*496+t]=order.size();std::vector<Entry>row;row.reserve(terminal[t].size());unsigned index=0;for(auto e:terminal[t]){int bound=dist[s*160+e.first]+int(e.second)*12;if(bound<INT16_MIN||bound>INT16_MAX||index>=256)throw std::runtime_error("Terminal dual bound range");row.push_back({int16_t(bound),uint8_t(index++)});}std::sort(row.begin(),row.end(),[](auto a,auto b){return a.reduced!=b.reduced?a.reduced<b.reduced:a.ordinal<b.ordinal;});order.insert(order.end(),row.begin(),row.end());}
  }
  std::cerr<<"directional_terminal_bound_entries="<<order.size()<<" negative_cycles=0\n";
 }
 const Entry*begin(unsigned source,unsigned target,unsigned d)const{return order.data()+starts[(d*160+source)*496+target];}
 unsigned size(unsigned target)const{return counts[target];}
 int lower(unsigned source,unsigned target,int dx,int dy)const{auto d=direction(dx,dy);if(!counts[target])return 1000000000;return ceil12(geometry(d,dx,dy)+begin(source,target,d)->reduced);}
};
