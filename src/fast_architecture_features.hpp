#pragma once
#include "routing_search.hpp"
#include <memory>
// Shared endpoint/graph features; no learned model or request labels here.
class FastArchitectureFeatures {
 std::array<int,496>family{};
 struct Topology {
  std::array<uint32_t,496*496>distance;std::array<archdata::XY,496>first{},last{};
  std::array<std::array<uint32_t,4>,496>access,terminal,long_access,long_terminal;
  Topology(){distance.fill(10000000);for(int p=0;p<496;++p)distance[p*496+p]=0;for(auto a:archdata::ARCS)distance[a.from*496+a.to]=std::min(distance[a.from*496+a.to],uint32_t(a.delay));for(auto n:archdata::NETS){distance[n.from*496+n.to]=std::min(distance[n.from*496+n.to],uint32_t(n.delay));first[n.from]=last[n.to]=archdata::VECTORS[n.vector];}
   for(int k=0;k<496;++k)for(int i=0;i<496;++i)for(int j=0;j<496;++j)distance[i*496+j]=std::min(distance[i*496+j],distance[i*496+k]+distance[k*496+j]);
   for(int i=0;i<496;++i){access[i].fill(10000000);terminal[i].fill(10000000);long_access[i].fill(10000000);long_terminal[i].fill(10000000);}
   for(auto n:archdata::NETS){auto v=archdata::VECTORS[n.vector];int dir=v.x>0?0:v.x<0?1:v.y>0?2:3;for(int p=0;p<496;++p){auto ac=distance[p*496+n.from],te=distance[n.to*496+p];access[p][dir]=std::min(access[p][dir],ac);terminal[p][dir]=std::min(terminal[p][dir],te);if(std::abs(v.x)+std::abs(v.y)>=10){long_access[p][dir]=std::min(long_access[p][dir],ac);long_terminal[p][dir]=std::min(long_terminal[p][dir],te);}}}
  }
 };
 std::unique_ptr<Topology>topology;
 void augment(std::array<float,71>&x,Node source,Node target)const{
  if(!topology)return;auto&g=*topology;auto a=archdata::SITES[source/496],b=archdata::SITES[target/496];int sp=source%496,tp=target%496;auto f=g.first[sp],l=g.last[tp];int rx=b.x-a.x-f.x-l.x,ry=b.y-a.y-f.y-l.y;auto mod=[](int n,int p){return (n%p+p)%p;};
  std::array<float,42>v={float(f.x),float(f.y),float(l.x),float(l.y),float(rx),float(ry),float(std::abs(rx)),float(std::abs(ry)),float(mod(rx,12)),float(mod(ry,12)),float(mod(rx,4)),float(mod(ry,4)),float(sp%8),float(tp%8),float(g.distance[sp*496+tp]),float(g.access[sp][0]),float(g.access[sp][1]),float(g.access[sp][2]),float(g.access[sp][3]),float(g.terminal[tp][0]),float(g.terminal[tp][1]),float(g.terminal[tp][2]),float(g.terminal[tp][3]),float(std::min(a.x,119-a.x)),float(std::min(a.y,549-a.y)),float(std::min(b.x,119-b.x)),float(std::min(b.y,549-b.y)),float(mod(a.x+f.x,10)),float(mod(b.x-l.x,10)),float(mod(a.y+f.y,12)),float(mod(b.y-l.y,12)),float(mod(rx,10)),float(std::abs(rx)%10),float(std::abs(ry)%12),float(g.long_access[sp][0]),float(g.long_access[sp][1]),float(g.long_access[sp][2]),float(g.long_access[sp][3]),float(g.long_terminal[tp][0]),float(g.long_terminal[tp][1]),float(g.long_terminal[tp][2]),float(g.long_terminal[tp][3])};std::copy(v.begin(),v.end(),x.begin()+29);
 }
public:
 explicit FastArchitectureFeatures(bool full=true){if(full)topology=std::make_unique<Topology>();
  std::vector<std::string>names;std::array<std::string,496>portfamily;for(int p=0;p<496;++p){std::string s=archdata::PORTS[p];portfamily[p]=s[0]=='Z'?s.substr(0,s.find('[')):s.substr(0,1);names.push_back(portfamily[p]);}std::sort(names.begin(),names.end());names.erase(std::unique(names.begin(),names.end()),names.end());for(int p=0;p<496;++p)family[p]=std::lower_bound(names.begin(),names.end(),portfamily[p])-names.begin();
 }
 std::array<float,71> get(Node source,Node target,Distance lower,const PhaseLowerBound&bounds)const {
  auto a=archdata::SITES[source/496],b=archdata::SITES[target/496];int dx=b.x-a.x,dy=b.y-a.y,sp=source%496,tp=target%496;float vg=float(bounds.gaps(a,{b.x,a.y})),hg=float(bounds.gaps(a,{a.x,b.y}));auto mod=[](int n,int p){return (n%p+p)%p;};
  std::array<float,71>x={float(a.x),float(a.y),float(b.x),float(b.y),float(dx),float(dy),float(std::abs(dx)),float(std::abs(dy)),float(std::abs(dx)+std::abs(dy)),float(sp),float(tp),float(family[sp]),float(family[tp]),float((dx>0)-(dx<0)),float((dy>0)-(dy<0)),float(a.x%10),float(b.x%10),float(a.y%12),float(b.y%12),vg,hg,float(lower),float(lower)-12.5f*std::abs(dx)-(125.f/12)*std::abs(dy)-vg-hg,float(mod(dx,10)),float(mod(dy,12)),float(mod(dx,4)),float(mod(dy,4)),float(sp%8),float(tp%8)};
  augment(x,source,target);
  return x;
 }
};
