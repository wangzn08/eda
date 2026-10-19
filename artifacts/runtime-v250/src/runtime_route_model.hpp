#pragma once
#include "runtime_short_kernel.hpp"
#include "compact_response_kernel.hpp"
#include "compact_phi_model.hpp"
#include "initial_kernel_candidates.hpp"
#ifndef RUNTIME_FEATURE_SCHEMA_HEADER
#define RUNTIME_FEATURE_SCHEMA_HEADER "selected_feature_schema.hpp"
#endif
#include RUNTIME_FEATURE_SCHEMA_HEADER
#include "selected_physics_features.hpp"
#include "directional_terminal_bounds.hpp"
#include "terminal_mask_catalog.hpp"
#include "terminal_interval_mask_catalog.hpp"
#include "architecture_operator_cache.hpp"
#ifndef RUNTIME_OPERATOR_CACHE
#define RUNTIME_OPERATOR_CACHE 0
#endif
#ifndef RUNTIME_INTERVAL_MASKS
#define RUNTIME_INTERVAL_MASKS 0
#endif
using ActiveTerminalMaskCatalog=std::conditional_t<RUNTIME_INTERVAL_MASKS,TerminalIntervalMaskCatalog,TerminalMaskCatalog>;
#include <memory>
#ifndef RUNTIME_SOURCE_LOWER_PRUNE
#define RUNTIME_SOURCE_LOWER_PRUNE 0
#endif
#ifndef RUNTIME_TERMINAL_LOWER_PRUNE
#define RUNTIME_TERMINAL_LOWER_PRUNE 0
#endif
#ifndef RUNTIME_FOREST_MODE
#define RUNTIME_FOREST_MODE 0
#endif
#ifndef RUNTIME_COMPILED_FOREST
#define RUNTIME_COMPILED_FOREST 0
#endif
#ifndef RUNTIME_TERMINAL_MASKS
#define RUNTIME_TERMINAL_MASKS 0
#endif
#ifndef RUNTIME_CORRECTION_GATE
#define RUNTIME_CORRECTION_GATE 0
#endif
struct KernelTrace{Node site=0;int core=-1,end=-1,entry=0,nominal=0,arc=0,kind=-1;};
struct PreparedKernelBranch{RuntimeShortKernel::View short_normal,short_crossed;CompactResponseKernel::View long_normal,long_crossed;int dx=0,dy=0,gap=0;bool cross=false,blocked=false,is_short=false,mask_usable=false;uint32_t normal_set=UINT32_MAX,cross_set=UINT32_MAX,cached_result=0;uint64_t operator_key=0;bool operator_hit=false;};
struct PreparedKernelRequest:KernelRequest{std::array<PreparedKernelBranch,32>prepared;uint32_t valid_vectors=0;};
class RuntimeRouteModel{
 const Graph&graph;RuntimeShortKernel short_kernel;CompactResponseKernel far_kernel,near_kernel;InitialKernelCandidates initial;CompactPhiModel phi;std::unique_ptr<DirectionalTerminalBounds>terminal_bounds;std::unique_ptr<ActiveTerminalMaskCatalog>terminal_masks;ArchitectureOperatorCache operator_cache{RUNTIME_OPERATOR_CACHE!=0};mutable uint64_t operator_hits=0,operator_misses=0;
 std::array<int,120>xgap{};std::array<int,550>ygap{};
 struct ForestNode{uint16_t feature,left,right,flags;double number;};static_assert(sizeof(ForestNode)==16);std::vector<std::vector<ForestNode>>forest;
public:
 RuntimeRouteModel(const Graph&g,const std::string&folder):graph(g),short_kernel({1,3,6,9}),far_kernel(folder+"/far-curves.bin"),near_kernel(folder+"/near-curves.bin"),initial(g,folder+"/source-hints.bin"),phi(folder+"/phi-patterns.bin"){
  if(RUNTIME_SOURCE_LOWER_PRUNE||RUNTIME_TERMINAL_LOWER_PRUNE)terminal_bounds=std::make_unique<DirectionalTerminalBounds>(initial.terminals);
  if(RUNTIME_TERMINAL_MASKS)terminal_masks=std::make_unique<ActiveTerminalMaskCatalog>(short_kernel,near_kernel,far_kernel,initial.terminals);
  if(far_kernel.horizontal_anchors()!=std::vector<unsigned>{1,3,6,9})throw std::runtime_error("Runtime anchor mismatch");for(auto l:archdata::LINES){if(l.vertical)for(int x=l.site+1;x<120;++x)xgap[x]+=l.delay;else for(int y=l.site+1;y<550;++y)ygap[y]+=l.delay;}
  std::ifstream f(folder+"/correction.bin",std::ios::binary);std::array<char,144>h;f.read(h.data(),h.size());uint32_t nf,nt;std::memcpy(&nf,h.data()+136,4);std::memcpy(&nt,h.data()+140,4);if(!f||std::memcmp(h.data(),"SFRST001",8)||std::memcmp(h.data()+8,archdata::HASH,64)||std::memcmp(h.data()+72,selectedschema::HASH,64)||nf!=selectedschema::COUNT||!nt||nt>64)throw std::runtime_error("Selected forest header");
  for(unsigned t=0;t<nt;++t){uint32_t n;f.read(reinterpret_cast<char*>(&n),4);if(!f||!n||n>=65536)throw std::runtime_error("Selected forest size");std::vector<ForestNode>tree(n);f.read(reinterpret_cast<char*>(tree.data()),n*16);if(!f)throw std::runtime_error("Selected forest body");for(unsigned i=0;i<n;++i){auto v=tree[i];if(!std::isfinite(v.number)||v.flags||(v.feature!=65535&&(v.feature>=selectedschema::COUNT||v.left<=i||v.right<=i||v.left>=n||v.right>=n)))throw std::runtime_error("Selected forest node");}forest.push_back(std::move(tree));}if(f.peek()!=EOF)throw std::runtime_error("Selected forest trailer");

#if RUNTIME_COMPILED_FOREST
  uint64_t checksum=1469598103934665603ull;for(const auto&tree:forest)for(size_t i=0;i<tree.size()*sizeof(ForestNode);++i){checksum^=reinterpret_cast<const unsigned char*>(tree.data())[i];checksum*=1099511628211ull;}if(checksum!=compiled_forest_checksum||forest.size()!=compiled_forest_count)throw std::runtime_error("Compiled forest asset mismatch");
#endif
  if(RUNTIME_OPERATOR_CACHE)operator_cache.initialize();runtime_memory_checkpoint("runtime-ready");
 }
 int cost(unsigned s,unsigned t,int dx,int dy)const{if(std::abs(dy)<96)return short_kernel.cost(s,t,dx,dy);return std::abs(dx)<=29?near_kernel.cost(s,t,dx,dy):far_kernel.cost(s,t,dx,dy);}
 int lower_bound(unsigned source,unsigned target,int dx,int dy)const{return terminal_bounds->lower(source,target,dx,dy);}
 void prepare(Node from,Node to,PreparedKernelRequest&r,bool force_all=false)const{
  initial.prepare(graph,from,to,r,force_all);auto target=archdata::SITES[r.to/496];unsigned tp=r.to%496;r.valid_vectors=graph.reverse_vector_mask(r.to/496);bool usable=RUNTIME_TERMINAL_MASKS&&terminal_masks->usable(tp,r.valid_vectors);uint32_t full=(1u<<initial.terminals[tp].size())-1;
  struct Geometry{Node site;int dx,dy,gap;bool cross,blocked;uint64_t key_stem;};std::array<Geometry,16>geometries;uint32_t seen_vectors=0;
  for(unsigned i=0;i<r.count;++i){auto b=r.branches[i];unsigned vector=archdata::NETS[b.core].vector;auto&g=geometries[vector];if(!(seen_vectors&(1u<<vector))||g.site!=b.site){seen_vectors|=1u<<vector;g.site=b.site;auto a=archdata::SITES[b.site];g.dx=target.x-a.x;g.dy=target.y-a.y;g.cross=std::min(a.x,target.x)<76&&std::max(a.x,target.x)>89;g.blocked=false;if(g.cross)for(auto block:archdata::BLOCKS)if(block.left==76&&block.right==89&&a.y>=block.lower&&a.y<=block.upper&&target.y>=block.lower&&target.y<=block.upper)g.blocked=true;g.gap=std::abs(xgap[a.x]-xgap[target.x])+std::abs(ygap[a.y]-ygap[target.y]);if(RUNTIME_OPERATOR_CACHE)g.key_stem=ArchitectureOperatorCache::key(0,tp,g.dx,g.dy,g.cross,g.blocked)-1;}auto&p=r.prepared[i];p.dx=g.dx;p.dy=g.dy;p.cross=g.cross;p.blocked=g.blocked;p.gap=g.gap;p.operator_hit=false;p.is_short=std::abs(p.dy)<96;p.mask_usable=usable;p.normal_set=full;p.cross_set=p.cross?full:0;if(RUNTIME_OPERATOR_CACHE){p.operator_key=(g.key_stem|b.core)+1;operator_cache.prefetch(p.operator_key,r.valid_vectors);continue;}int cx=p.dx+(p.dx>0?-14:14);
   if(p.is_short){p.short_normal=short_kernel.view(b.core,p.dx,p.dy);if(p.cross)p.short_crossed=short_kernel.view(b.core,cx,p.dy);}else{auto one=[&](int x){return std::abs(x)<=29?near_kernel.view(b.core,x,p.dy):far_kernel.view(b.core,x,p.dy);};p.long_normal=one(p.dx);if(p.cross)p.long_crossed=one(cx);}
   if(usable){terminal_masks->prefetch(b.core,tp,p.dx,p.dy);if(p.cross)terminal_masks->prefetch(b.core,tp,cx,p.dy);}
  }
 }
 void resolve_operator_cache(PreparedKernelRequest&r)const{
  if(!RUNTIME_OPERATOR_CACHE)return;unsigned tp=r.to%496;for(unsigned i=0;i<r.count;++i){auto&p=r.prepared[i];auto b=r.branches[i];p.operator_hit=operator_cache.get(p.operator_key,r.valid_vectors,p.cached_result);if(p.operator_hit){++operator_hits;continue;}++operator_misses;int cx=p.dx+(p.dx>0?-14:14);if(p.is_short){p.short_normal=short_kernel.view(b.core,p.dx,p.dy);if(p.cross)p.short_crossed=short_kernel.view(b.core,cx,p.dy);}else{auto one=[&](int x){return std::abs(x)<=29?near_kernel.view(b.core,x,p.dy):far_kernel.view(b.core,x,p.dy);};p.long_normal=one(p.dx);if(p.cross)p.long_crossed=one(cx);}if(p.mask_usable){terminal_masks->prefetch(b.core,tp,p.dx,p.dy);if(p.cross)terminal_masks->prefetch(b.core,tp,cx,p.dy);}}
 }
 void prefetch(PreparedKernelRequest&r)const{
  unsigned tp=r.to%496;for(unsigned i=0;i<r.count;++i){auto&p=r.prepared[i];if(p.operator_hit)continue;auto b=r.branches[i];if(p.mask_usable){p.normal_set=terminal_masks->get(b.core,tp,p.dx,p.dy);if(p.cross)p.cross_set=terminal_masks->get(b.core,tp,p.dx+(p.dx>0?-14:14),p.dy);}
   auto warm=[&](const auto&normal,const auto&crossed){if(p.mask_usable||initial.terminals[tp].size()==1){uint32_t choices=(p.blocked?0:p.normal_set)|p.cross_set;while(choices){unsigned ordinal=__builtin_ctz(choices);choices&=choices-1;unsigned end=initial.terminals[tp][ordinal].first,bit=1u<<ordinal;if(!p.blocked&&(p.normal_set&bit))normal.prefetch_target(end);if(p.cross_set&bit)crossed.prefetch_target(end);}}else{if(!p.blocked)normal.prefetch();if(p.cross)crossed.prefetch();}};
   if(p.is_short)warm(p.short_normal,p.cross?p.short_crossed:p.short_normal);else warm(p.long_normal,p.cross?p.long_crossed:p.long_normal);
  }
 }
 void prefetch_selected_codes(const KernelRequest&r,const KernelTrace&t)const{if(t.core>=0){phi.prefetch_code(t.site,t.core);phi.prefetch_code(r.to/496,t.end);}}
 void prefetch_selected_patterns(const KernelRequest&r,const KernelTrace&t)const{if(t.core>=0){phi.prefetch_pattern(t.site,t.core);phi.prefetch_pattern(r.to/496,t.end);}}
 void prefetch_selected_features(const KernelRequest&r,const KernelTrace&t)const{
  if(t.core<0)return;
  auto a=archdata::SITES[t.site],z=archdata::SITES[r.to/496];int dx=z.x-a.x,dy=z.y-a.y,x=dx-(t.kind==2?((dx>0)-(dx<0))*14:0),q=std::abs(dy)/12,phase=std::abs(dy)%12,sg=dy<0?-1:1;
  auto one=[&](int period){int y=sg*(period*12+phase);if(std::abs(y)<96)short_kernel.view(t.core,x,y).prefetch_target(t.end);else if(std::abs(x)<=29)near_kernel.view(t.core,x,y).prefetch_target(t.end);else far_kernel.view(t.core,x,y).prefetch_target(t.end);};one(0);one(2);one(8);if(q&&q-1<8&&q-1!=0&&q-1!=2)one(q-1);if(q<7&&q+1!=2)one(q+1);
 }
 int base(const PreparedKernelRequest&r,KernelTrace&trace)const{
  int best=r.local;trace={r.from/496,-1,-1,0,best,0,-1};auto target=archdata::SITES[r.to/496];unsigned tp=r.to%496;uint32_t mask=r.valid_vectors;
  struct Rank{unsigned i;int value;};std::array<Rank,32>ranking;for(unsigned i=0;RUNTIME_SOURCE_LOWER_PRUNE&&i<r.count;++i){ranking[i]={i,0};if(r.count>1){auto branch=r.branches[i];auto a=archdata::SITES[branch.site];int dx=target.x-a.x,dy=target.y-a.y;bool cross=std::min(a.x,target.x)<76&&std::max(a.x,target.x)>89,blocked=false;if(cross)for(auto b:archdata::BLOCKS)if(b.left==76&&b.right==89&&a.y>=b.lower&&a.y<=b.upper&&target.y>=b.lower&&target.y<=b.upper)blocked=true;int lb=blocked?1000000000:lower_bound(branch.core,tp,dx,dy);if(cross)lb=std::min(lb,lower_bound(branch.core,tp,dx+(dx>0?-14:14),dy)+292);ranking[i].value=lb+branch.entry+std::abs(xgap[a.x]-xgap[target.x])+std::abs(ygap[a.y]-ygap[target.y]);}}if(RUNTIME_SOURCE_LOWER_PRUNE&&r.count>1)std::sort(ranking.begin(),ranking.begin()+r.count,[](auto a,auto b){return a.value<b.value;});
  for(unsigned k=0;k<r.count;++k){if(RUNTIME_SOURCE_LOWER_PRUNE&&r.count>1&&ranking[k].value>best)break;unsigned index=RUNTIME_SOURCE_LOWER_PRUNE?ranking[k].i:k;auto branch=r.branches[index];const auto&p=r.prepared[index];int dx=p.dx,dy=p.dy;bool cross=p.cross,blocked=p.blocked;
   if(p.operator_hit){uint32_t word=p.cached_result;int nominal=ArchitectureOperatorCache::nominal(word),value=nominal+branch.entry+p.gap;if(value<best||(value==best&&trace.core>=0&&branch.core<trace.core)){best=value;trace={branch.site,int(branch.core),int(ArchitectureOperatorCache::end(word)),branch.entry,nominal,int(ArchitectureOperatorCache::arc(word)),int(ArchitectureOperatorCache::kind(word))};}continue;}
   int nominal=1000000000,end=-1,arc=0,kind=0;unsigned selected_ordinal=256;auto evaluate=[&](const auto&normal,const auto&crossed){if(!RUNTIME_TERMINAL_LOWER_PRUNE){uint32_t normal_set=p.normal_set,cross_set=p.cross_set;uint32_t choices=(blocked?0:normal_set)|(cross?cross_set:0);while(choices){unsigned ordinal=__builtin_ctz(choices);choices&=choices-1;auto e=initial.terminals[tp][ordinal];unsigned bit=1u<<ordinal;if((mask&(1u<<archdata::NETS[e.first].vector))||(dx==0&&dy==0&&branch.core==e.first)){int v=blocked||!(normal_set&bit)?1000000000:normal.get(e.first)+int(e.second),k=0;if(cross&&(cross_set&bit)){int w=crossed.get(e.first)+int(e.second)+292;if(w<v){v=w;k=2;}}if(v<nominal){nominal=v;end=e.first;arc=e.second;kind=k;selected_ordinal=ordinal;}}}return;}unsigned d=DirectionalTerminalBounds::direction(dx,dy);int normal_geo=DirectionalTerminalBounds::geometry(d,dx,dy),cross_geo=DirectionalTerminalBounds::geometry(d,dx+(dx>0?-14:14),dy);const auto*sorted=terminal_bounds->begin(branch.core,tp,d);for(unsigned j=0;j<terminal_bounds->size(tp);++j){auto b=sorted[j];int normal_lb=DirectionalTerminalBounds::ceil12(normal_geo+b.reduced),cross_lb=DirectionalTerminalBounds::ceil12(cross_geo+b.reduced)+292;if((blocked?cross_lb:normal_lb)>nominal)break;auto e=initial.terminals[tp][b.ordinal];if(!(mask&(1u<<archdata::NETS[e.first].vector))&&!(dx==0&&dy==0&&branch.core==e.first))continue;auto consider=[&](int value,int k){if(value<nominal||(value==nominal&&unsigned(b.ordinal)<selected_ordinal)){nominal=value;end=e.first;arc=e.second;kind=k;selected_ordinal=b.ordinal;}};if(!blocked&&normal_lb<=nominal)consider(normal.get(e.first)+int(e.second),0);if(cross&&cross_lb<=nominal)consider(crossed.get(e.first)+int(e.second)+292,2);}};
   if(p.is_short)evaluate(p.short_normal,p.cross?p.short_crossed:p.short_normal);else evaluate(p.long_normal,p.cross?p.long_crossed:p.long_normal);
   if(end<0)continue;if(RUNTIME_OPERATOR_CACHE)operator_cache.put(p.operator_key,r.valid_vectors,nominal,end,arc,kind);int value=nominal+branch.entry+p.gap;if(value<best||(value==best&&trace.core>=0&&branch.core<trace.core)){best=value;trace={branch.site,int(branch.core),end,branch.entry,nominal,arc,kind};}
  }
  if(best>=1000000000&&r.mask!=UINT32_MAX){PreparedKernelRequest all;prepare(r.from,r.to,all,true);resolve_operator_cache(all);prefetch(all);return base(all,trace);}if(best>=1000000000)throw std::runtime_error("Unreachable runtime query");return best;
 }
 class Features{
  const RuntimeRouteModel&model;const KernelRequest&r;const KernelTrace&t;int b,sx,sy,tx,ty,ox,oy,sp,tp,dx,dy,ax,ay,qx,qy,gx,gy,direction,backward;bool valid,cross;std::array<float,selectedschema::COUNT>cached;std::array<uint64_t,(selectedschema::COUNT+63)/64>seen{};const int16_t*source_phi=nullptr,*target_phi=nullptr;
  static int sign(int x){return (x>0)-(x<0);}
  float phi_value(bool source,unsigned index){if(!valid)return 0;auto&ptr=source?source_phi:target_phi;if(!ptr)ptr=model.phi.row(source?t.site:r.to/496,source?t.core:t.end);return float(double(ptr[index])/12.0);}
  int response(unsigned j)const{if(!valid)return 0;int x=dx-(t.kind==2?sign(dx)*14:0),slope=dy<0?125:127,sg=dy<0?-1:1,ry=ay%12;auto query=[&](int q){return model.cost(t.core,t.end,x,sg*(q*12+ry))-q*slope;};if(j<6){const int periods[6]={0,2,8,20,32,45};return query(periods[j]);}int current=t.nominal-t.arc-(t.kind==2?292:0)-qy*slope;if(j==6)return qy?current-query(qy-1):0;return qy<45?query(qy+1)-current:0;}
  __attribute__((always_inline)) float calculate(unsigned i){if(i>=137)return selectedphysics::value(*this,i-137);if(i>=77&&i<101)return phi_value(true,i-77);if(i>=101&&i<125)return phi_value(false,i-101);if(i>=125){bool source=i<131;unsigned j=i-(source?125:131);return phi_value(source,(j/3)*12+(j%3)*4+(source?direction:backward));}if(i>=69)return response(i-69);if(i>=63){if(!valid)return 0;unsigned core=i<66?t.core:t.end,j=(i-63)%3;auto e=archdata::NETS[core];auto v=archdata::VECTORS[e.vector];return j==0?v.x:j==1?v.y:e.delay;}
   switch(i){case 0:return b;case 1:return sx;case 2:return sy;case 3:return tx;case 4:return ty;case 5:return ox;case 6:return oy;case 7:return sp;case 8:return tp;case 9:return selectedschema::PORT_TYPE[sp];case 10:return selectedschema::PORT_TYPE[tp];case 11:return selectedschema::PORT_LANE[sp];case 12:return selectedschema::PORT_LANE[tp];case 13:return t.core;case 14:return t.end;case 15:return valid?t.core%20:-1;case 16:return valid?t.end%20:-1;case 17:return valid?t.core/20:-1;case 18:return valid?t.end/20:-1;case 19:return dx;case 20:return dy;case 21:return ax;case 22:return ay;case 23:return qx;case 24:return qy;case 25:return sign(dx)*(ax-qx*10);case 26:return sign(dy)*(ay%12);case 27:return sx%10;case 28:return sy%12;case 29:return tx%10;case 30:return ty%12;case 31:return sy%100;case 32:return ty%100;case 33:return sy/100;case 34:return ty/100;case 35:return std::min(sx,119-sx);case 36:return std::min(tx,119-tx);case 37:return std::min(sy,549-sy);case 38:return std::min(ty,549-ty);case 39:return std::min(sy%100,99-sy%100);case 40:return std::min(ty%100,99-ty%100);case 41:return sx-ox;case 42:return sy-oy;case 43:return t.entry;case 44:return valid?t.nominal:b;case 45:return t.arc;case 46:return t.kind;case 47:return valid;case 48:return (valid?t.nominal:b)-125*qx-(dy>0?127:125)*qy;case 49:return valid?b-t.entry-t.nominal:0;case 50:return gx;case 51:return gy;case 52:return std::abs(gx);case 53:return std::abs(gy);case 54:return cross;case 55:return sx>=76&&sx<=89;case 56:return tx>=76&&tx<=89;case 57:{int n=0;for(int y=0;y<450;y+=100)n+=std::min(sy,ty)<y+49&&std::max(sy,ty)>y;return n;}case 58:return std::min(sx-75,90-sx);case 59:return std::min(tx-75,90-tx);case 60:return std::max(0,16-std::min(sx,tx));case 61:return std::max(0,100-std::min(sy,ty));case 62:return cross&&sy/100==ty/100&&sy%100<=49&&ty%100<=49;default:throw std::runtime_error("Feature index");}
  }
 public:
  Features(const RuntimeRouteModel&m,const KernelRequest&request,const KernelTrace&trace,int value):model(m),r(request),t(trace),b(value){auto a=archdata::SITES[t.site],target=archdata::SITES[r.to/496],original=archdata::SITES[r.from/496];sx=a.x;sy=a.y;tx=target.x;ty=target.y;ox=original.x;oy=original.y;sp=r.from%496;tp=r.to%496;dx=tx-sx;dy=ty-sy;ax=std::abs(dx);ay=std::abs(dy);qx=ax>29?(ax-20)/10:0;qy=ay/12;gx=m.xgap[tx]-m.xgap[sx];gy=m.ygap[ty]-m.ygap[sy];valid=t.core>=0;cross=std::min(sx,tx)<76&&std::max(sx,tx)>89;direction=(dx<0)*2+(dy<0);backward=(dx>=0)*2+(dy>=0);}
  float get(unsigned i){uint64_t bit=uint64_t(1)<<(i%64);if(!(seen[i/64]&bit)){cached[i]=calculate(i);seen[i/64]|=bit;}return cached[i];}
  template<unsigned i>int integer(){static_assert(i<selectedschema::COUNT);if constexpr(i>=137)return selectedphysics::integer<i-137>(*this);else if constexpr(i>=77){if(!valid)return 0;constexpr bool source=i<101||(i>=125&&i<131);unsigned index;if constexpr(i<101)index=i-77;else if constexpr(i<125)index=i-101;else {constexpr unsigned j=i-(source?125:131);index=(j/3)*12+(j%3)*4+(source?direction:backward);}auto&ptr=source?source_phi:target_phi;if(!ptr)ptr=model.phi.row(source?t.site:r.to/496,source?t.core:t.end);return ptr[index];}else if constexpr(i>=69)return int(get(i));else return int(calculate(i));}
  void eager(){for(unsigned i=0;i<77;++i)cached[i]=calculate(i);for(unsigned i=0;i<24;++i){cached[77+i]=phi_value(true,i);cached[101+i]=phi_value(false,i);}for(unsigned j=0;j<6;++j){unsigned index=(j/3)*12+(j%3)*4;cached[125+j]=cached[77+index+direction];cached[131+j]=cached[101+index+backward];}for(unsigned i=0;i<137;++i)seen[i/64]|=uint64_t(1)<<(i%64);for(unsigned i=137;i<selectedschema::COUNT;++i)cached[i]=calculate(i);seen.fill(UINT64_MAX);}
  std::array<float,selectedschema::COUNT>dense(){for(unsigned i=0;i<selectedschema::COUNT;++i)get(i);return cached;}
 };
#if RUNTIME_COMPILED_FOREST
 #ifndef RUNTIME_COMPILED_FOREST_HEADER
 #define RUNTIME_COMPILED_FOREST_HEADER "compiled_selected_forest.hpp"
 #endif
 #include RUNTIME_COMPILED_FOREST_HEADER
#endif
#if RUNTIME_CORRECTION_GATE
 #ifndef RUNTIME_CORRECTION_GATE_HEADER
 #define RUNTIME_CORRECTION_GATE_HEADER "compiled_selected_correction_gate.hpp"
 #endif
 #include RUNTIME_CORRECTION_GATE_HEADER
#endif
 bool needs_correction(const KernelRequest&r,const KernelTrace&t,int value)const{
#if RUNTIME_CORRECTION_GATE
 Features row(*this,r,t,value);return compiled_needs_correction(row);
#else
 return true;
#endif
 }
 int correct(const KernelRequest&r,const KernelTrace&trace,int value,std::array<float,selectedschema::COUNT>*features=nullptr)const{Features row(*this,r,trace,value);double correction=0;
#if RUNTIME_COMPILED_FOREST
 correction=compiled_correction(row);
#else
 if(RUNTIME_FOREST_MODE)row.eager();if(RUNTIME_FOREST_MODE==2){std::array<unsigned,64>indices{};unsigned active=forest.size();while(active){active=0;for(unsigned t=0;t<forest.size();++t){auto n=forest[t][indices[t]];if(n.feature!=65535){indices[t]=double(row.get(n.feature))<=n.number?n.left:n.right;++active;}}}for(unsigned t=0;t<forest.size();++t)correction+=forest[t][indices[t]].number;}else{for(const auto&tree:forest){unsigned i=0;while(tree[i].feature!=65535){auto n=tree[i];i=double(row.get(n.feature))<=n.number?n.left:n.right;}correction+=tree[i].number;}}
#endif
 if(features)*features=row.dense();return int(std::nearbyint(std::max(0.,double(value)+correction)));}
 void report_operator_cache()const{if(RUNTIME_OPERATOR_CACHE)std::cerr<<"architecture_operator_cache_bytes="<<operator_cache.bytes()<<" hits="<<operator_hits<<" misses="<<operator_misses<<" final_prediction_cache=0\n";}
 int predict(PreparedKernelRequest&r,KernelTrace*diagnostic=nullptr,std::array<float,selectedschema::COUNT>*features=nullptr,int*baseline=nullptr)const{resolve_operator_cache(r);prefetch(r);KernelTrace trace;int value=base(r,trace);if(diagnostic)*diagnostic=trace;if(baseline)*baseline=value;if(!needs_correction(r,trace,value)){if(features){Features row(*this,r,trace,value);*features=row.dense();}return value;}return correct(r,trace,value,features);}
};
