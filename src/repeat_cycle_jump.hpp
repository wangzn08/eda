#pragma once
#include "routing_search.hpp"
// Architecture-only doubling table: every entry composes actual local-arc/Net moves.
class RepeatCycleJump {
public:
 struct Result {Node site=NONE;uint32_t delay=0;};
 struct Cycle {unsigned port;int net;uint32_t cost;};
 std::vector<Cycle> cycles;
private:
 std::vector<Result> table;
 size_t sites;
 static constexpr unsigned levels=6;
 size_t offset(unsigned cycle,unsigned level,Node site)const{return (size_t(cycle)*levels+level)*sites+site;}
public:
 explicit RepeatCycleJump(const Graph&graph):sites(graph.sites()){
  for(size_t n=0;n<std::size(archdata::NETS);++n){auto net=archdata::NETS[n];auto v=archdata::VECTORS[net.vector];if(std::abs(v.x)+std::abs(v.y)<10)continue;Distance cost=INF;for(auto a:graph.local_out(net.to))if(a.port==net.from)cost=std::min(cost,Distance(a.delay)+net.delay);if(cost<INF)cycles.push_back({unsigned(net.to),int(n),uint32_t(cost)});}
  table.resize(cycles.size()*levels*sites);
  for(unsigned c=0;c<cycles.size();++c){for(Node s=0;s<sites;++s){auto m=graph.net_move(s,cycles[c].net,false);if(m.site!=NONE)table[offset(c,0,s)]={m.site,m.delay+cycles[c].cost};}
   for(unsigned k=1;k<levels;++k)for(Node s=0;s<sites;++s){auto a=table[offset(c,k-1,s)];if(a.site==NONE)continue;auto b=table[offset(c,k-1,a.site)];if(b.site!=NONE)table[offset(c,k,s)]={b.site,a.delay+b.delay};}}
 }
 Result jump(unsigned cycle,Node site,unsigned repetitions)const{
  if(cycle>=cycles.size() || site>=sites || repetitions>=64)throw std::runtime_error("Invalid cycle jump");Result answer{site,0};
  for(unsigned k=0;repetitions;++k,repetitions>>=1)if(repetitions&1){auto next=table[offset(cycle,k,answer.site)];if(next.site==NONE)return {};answer.site=next.site;answer.delay+=next.delay;}return answer;
 }
 size_t bytes()const{return table.size()*sizeof(Result);}
};
