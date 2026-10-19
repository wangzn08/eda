#pragma once
#include <tuple>
// Research features from actual directed endpoint moves and a finite ideal
// suffix. Beam truncation and the suffix are approximate, not shortest-path
// certificates. No labels or request result cache enter this computation.
class EndpointBellmanProfile {
 struct Edge { uint16_t core,net; int cost; };
 struct State { Node site; unsigned core; int cost,rank; };
 const Graph& graph;
 std::array<int,496> index;
 std::array<std::vector<Edge>,160> forward,reverse;
 std::array<std::vector<std::pair<unsigned,int>>,496> terminals;
 std::array<int,120> xgap{};
 std::array<int,550> ygap{};
 static constexpr int large=1000000000;
 static void retain(std::vector<State>& rows,unsigned width) {
  std::sort(rows.begin(),rows.end(),[](const State&a,const State&b){
   return std::tie(a.rank,a.cost,a.site,a.core)<std::tie(b.rank,b.cost,b.site,b.core);
  });
  std::vector<State> unique;
  for(auto row:rows){bool seen=false;for(auto other:unique)seen|=row.site==other.site&&row.core==other.core;if(!seen)unique.push_back(row);if(unique.size()==width)break;}
  rows=std::move(unique);
 }
 template<class Model> int pair(const Model&model,const State&s,const State&t)const {
  if(s.site==t.site&&s.core==t.core)return s.cost+t.cost;
  if(!(graph.reverse_vector_mask(t.site)&(1u<<archdata::NETS[t.core].vector)))return large;
  auto a=archdata::SITES[s.site],b=archdata::SITES[t.site];int dx=b.x-a.x,dy=b.y-a.y;
  bool cross=std::min(a.x,b.x)<76&&std::max(a.x,b.x)>89,blocked=false;
  if(cross)for(auto block:archdata::BLOCKS)if(block.left==76&&block.right==89&&a.y>=block.lower&&a.y<=block.upper&&b.y>=block.lower&&b.y<=block.upper)blocked=true;
  int value=blocked?large:model.cost(s.core,t.core,dx,dy);
  if(cross)value=std::min(value,model.cost(s.core,t.core,dx+(dx>0?-14:14),dy)+292);
  return std::min(large,value+s.cost+t.cost+std::abs(xgap[a.x]-xgap[b.x])+std::abs(ygap[a.y]-ygap[b.y]));
 }
 template<class Model> int best(const Model&model,const std::vector<State>&s,const std::vector<State>&t)const {
  int value=large;for(auto a:s)values(model,a,t,[&](const State&,int v){value=std::min(value,v);});return value;
 }
 template<class Model,class Rows,class Visitor> void values(const Model&model,const State&s,Rows&t,Visitor visit)const {
  Node previous=NONE;typename Model::ResponseRow normal,crossed;int gap=0;bool cross=false,blocked=false;uint32_t valid=0;
  for(auto&target:t){if(target.site!=previous){previous=target.site;auto a=archdata::SITES[s.site],b=archdata::SITES[target.site];int dx=b.x-a.x,dy=b.y-a.y;gap=std::abs(xgap[a.x]-xgap[b.x])+std::abs(ygap[a.y]-ygap[b.y]);cross=std::min(a.x,b.x)<76&&std::max(a.x,b.x)>89;blocked=false;if(cross)for(auto block:archdata::BLOCKS)if(block.left==76&&block.right==89&&a.y>=block.lower&&a.y<=block.upper&&b.y>=block.lower&&b.y<=block.upper)blocked=true;
    if(!blocked)normal=model.response_row(s.core,dx,dy);if(cross)crossed=model.response_row(s.core,dx+(dx>0?-14:14),dy);valid=graph.reverse_vector_mask(target.site);
   }
   int value=large;
   if(s.site==target.site&&s.core==target.core)value=s.cost+target.cost;
   else if(valid&(1u<<archdata::NETS[target.core].vector)){int nominal=blocked?large:normal.get(target.core);if(cross)nominal=std::min(nominal,crossed.get(target.core)+292);value=std::min(large,nominal+s.cost+target.cost+gap);}
   visit(target,value);
  }
 }
 template<class Model> std::vector<State> extend(const Model&model,const std::vector<State>&front,const std::vector<State>&other,bool backwards,unsigned width,Node finish,unsigned port)const {
  std::vector<State> result;
  for(auto row:front){
   // A path that has already reached its endpoint must not be forced to leave.
   bool complete=false;for(auto tail:other)complete|=row.site==tail.site&&row.core==tail.core;
   if(complete)result.push_back(row);
   for(auto edge:(backwards?reverse:forward)[row.core]){
    auto moved=graph.net_move(row.site,edge.net,backwards);if(moved.site==NONE)continue;
    State next{moved.site,edge.core,row.cost+edge.cost+int(moved.delay),large};
    if(backwards){for(auto tail:other)next.rank=std::min(next.rank,pair(model,tail,next));}
    else values(model,next,other,[&](const State&,int v){next.rank=std::min(next.rank,v);});
    result.push_back(next);
   }
  }
  retain(result,width);return result;
 }
public:
 static constexpr unsigned count=16;
 explicit EndpointBellmanProfile(const Graph&g):graph(g){
  index.fill(-1);for(unsigned i=0;i<160;++i){index[archdata::NETS[i].to]=i;terminals[archdata::NETS[i].to].push_back({i,0});}
  for(auto arc:archdata::ARCS)if(index[arc.from]>=0){
   terminals[arc.to].push_back({unsigned(index[arc.from]),arc.delay});
   int net=graph.net_out(arc.to);if(net>=0){auto n=archdata::NETS[net];int u=index[arc.from],v=index[n.to],cost=arc.delay+n.delay;
    forward[u].push_back({uint16_t(v),uint16_t(net),cost});reverse[v].push_back({uint16_t(u),uint16_t(net),cost});}
  }
  for(auto line:archdata::LINES)if(line.vertical){for(int x=line.site+1;x<120;++x)xgap[x]+=line.delay;}else{for(int y=line.site+1;y<550;++y)ygap[y]+=line.delay;}
 }
 template<class Model> std::array<float,count> evaluate(const Model&model,const KernelRequest&r,int baseline,unsigned width=2,const KernelTrace*selected=nullptr,unsigned stages=31,bool seeded=false)const {
  std::vector<State>s,t;
#if RUNTIME_ENDPOINT_SEEDS
  if(seeded&&selected){for(unsigned i=0;i<selected->source_count;++i){auto a=selected->sources[i];s.push_back({a.site,a.core,a.cost,a.rank});}for(unsigned i=0;i<selected->target_count;++i){auto a=selected->targets[i];t.push_back({a.site,a.core,a.cost,a.rank});}}
  else
#endif
  if(selected&&selected->core>=0){s.push_back({selected->site,unsigned(selected->core),selected->entry,large});t.push_back({r.to/496,unsigned(selected->end),selected->arc,large});}
  else{for(unsigned i=0;i<r.count;++i){auto a=r.branches[i];s.push_back({a.site,a.core,a.entry,large});}
   for(auto a:terminals[r.to%496])t.push_back({r.to/496,a.first,a.second,large});}
  int raw=large;for(auto&a:s)values(model,a,t,[&](State&b,int value){a.rank=std::min(a.rank,value);b.rank=std::min(b.rank,value);raw=std::min(raw,value);});
  retain(s,width);retain(t,width);
  std::vector<State>s1,t1,s2,t2;
  if(stages&5)s1=extend(model,s,t,false,width,r.to/496,r.to%496);
  if(stages&10)t1=extend(model,t,s,true,width,r.from/496,r.from%496);
  if(stages&4)s2=extend(model,s1,t,false,width,r.to/496,r.to%496);
  if(stages&8)t2=extend(model,t1,s,true,width,r.from/496,r.from%496);
  std::array<float,count> out{};auto put=[&](unsigned k,int v){out[k]=std::clamp(v-baseline,-2000,2000);};
  put(0,raw);put(1,best(model,s,t));
  if(stages&1)put(2,best(model,s1,t));if(stages&2)put(3,best(model,s,t1));
  if(stages&4)put(4,best(model,s2,t));if(stages&8)put(5,best(model,s,t2));
  if(stages&16){put(6,best(model,s1,t1));put(7,best(model,s2,t1));put(8,best(model,s1,t2));put(9,best(model,s2,t2));}
  out[10]=s.size()>1?std::clamp(s[1].rank-s[0].rank,0,2000):2000;
  out[11]=t.size()>1?std::clamp(t[1].rank-t[0].rank,0,2000):2000;
  out[12]=s1.empty()?0:s1[0].cost;out[13]=t1.empty()?0:t1[0].cost;
  out[14]=s2.empty()?0:s2[0].cost;out[15]=t2.empty()?0:t2[0].cost;
  return out;
 }
};
