// Architecture-only single-source teacher. No validation/holdout label access.
#include "routing_search.hpp"
#include <fstream>
#include <iostream>
#include <random>
#include <ctime>
struct TeacherEdge {uint32_t to,cost;};
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("development seed IDs, output numeric CSV, targets per source required");
 const unsigned samples=std::stoul(argv[3]);if(samples>1000000)throw std::runtime_error("sample limit");
 Graph graph;auto begin=std::clock();std::array<int,archdata::P>index;index.fill(-1);unsigned count=0;
 for(auto net:archdata::NETS){if(index[net.to]>=0)throw std::runtime_error("duplicate core");index[net.to]=count++;}
 if(count!=160)throw std::runtime_error("core count");
 const uint64_t states=uint64_t(graph.sites())*count;if(states>UINT32_MAX)throw std::runtime_error("state overflow");
 struct Arc{unsigned from,to,vector,cost;};std::vector<Arc>arcs;
 std::array<std::vector<std::pair<unsigned,unsigned>>,archdata::P>terminal;
 for(unsigned p=0;p<archdata::P;++p){if(index[p]>=0)terminal[p].push_back({unsigned(index[p]),0});}
 for(auto arc:archdata::ARCS)if(index[arc.from]>=0){terminal[arc.to].push_back({unsigned(index[arc.from]),unsigned(arc.delay)});int ni=graph.net_out(arc.to);if(ni>=0){auto net=archdata::NETS[ni];arcs.push_back({unsigned(index[arc.from]),unsigned(index[net.to]),unsigned(net.vector),unsigned(arc.delay+net.delay)});}}
 std::vector<uint32_t>offset(states+1);uint64_t edges=0;
 for(Node s=0;s<graph.sites();++s)for(auto a:arcs){auto m=graph.forward_vector_move(s,a.vector);if(m.site!=NONE){++offset[s*count+a.from+1];++edges;}}
 if(edges>UINT32_MAX)throw std::runtime_error("edge overflow");for(unsigned u=0;u<states;++u)offset[u+1]+=offset[u];
 std::vector<TeacherEdge>adj(edges);auto cursor=offset;
 for(Node s=0;s<graph.sites();++s)for(auto a:arcs){auto m=graph.forward_vector_move(s,a.vector);if(m.site!=NONE)adj[cursor[s*count+a.from]++]={m.site*count+a.to,a.cost+m.delay};}
 cursor.clear();cursor.shrink_to_fit();std::cerr<<"states="<<states<<" edges="<<edges<<" graph_cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 std::ifstream seeds(argv[1]);if(!seeds)throw std::runtime_error("seed open");std::ofstream out(argv[2]);if(!out)throw std::runtime_error("output open");out<<"source,target,delay\n";
 constexpr uint32_t infinity=UINT32_MAX/4;std::vector<uint32_t>d(states);std::mt19937 rng(20261007);Node source;uint64_t rows=0;unsigned runs=0;
 struct Audit{Node source,target;uint32_t expected;};std::vector<Audit>audit;
 while(seeds>>source){if(source>=uint64_t(graph.sites())*archdata::P)throw std::runtime_error("source ID");std::fill(d.begin(),d.end(),infinity);using Item=std::pair<uint32_t,uint32_t>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>>q;
  auto add=[&](Node site,unsigned port,uint32_t cost){unsigned u=site*count+index[port];if(cost<d[u]){d[u]=cost;q.push({cost,u});}};
  Node ss=source/archdata::P;unsigned sp=source%archdata::P;
  if(index[sp]>=0)add(ss,sp,0);else if(int ni=graph.net_out(sp);ni>=0){auto m=graph.net_move(ss,ni,false);if(m.site!=NONE)add(m.site,archdata::NETS[ni].to,m.delay+archdata::NETS[ni].delay);}else for(auto a:graph.local_out(sp)){int ni=graph.net_out(a.port);if(ni>=0){auto m=graph.net_move(ss,ni,false);if(m.site!=NONE)add(m.site,archdata::NETS[ni].to,a.delay+m.delay+archdata::NETS[ni].delay);}}
  while(!q.empty()){auto[g,u]=q.top();q.pop();if(g!=d[u])continue;for(unsigned k=offset[u];k<offset[u+1];++k){auto e=adj[k];if(e.cost>=infinity-g)throw std::runtime_error("distance overflow");unsigned value=g+e.cost;if(value<d[e.to]){d[e.to]=value;q.push({value,e.to});}}}
  // Include only architecture-defined reachable endpoints; target sampling is deterministic.
  for(unsigned k=0;k<samples;++k){Node ts=rng()%graph.sites();unsigned tp=rng()%archdata::P;uint32_t best=infinity;for(auto e:terminal[tp])if(d[ts*count+e.first]<infinity-e.second)best=std::min(best,d[ts*count+e.first]+e.second);if(ts==ss){if(tp==sp)best=0;for(auto e:graph.local_out(sp))if(e.port==tp)best=std::min(best,e.delay);}if(best<infinity){Node target=ts*archdata::P+tp;out<<source<<','<<target<<','<<best<<'\n';++rows;if(runs<8&&k<4)audit.push_back({source,target,best});}}
  out.flush();++runs;std::cerr<<"sources="<<runs<<" rows="<<rows<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }
 if(!seeds.eof()||!out)throw std::runtime_error("CSV I/O");
 adj.clear();adj.shrink_to_fit();offset.clear();offset.shrink_to_fit();d.clear();d.shrink_to_fit();
 CompactSolver checker(graph);for(auto a:audit){SearchStats stats;auto value=checker.solve(a.source,a.target,stats);if(value!=a.expected)throw std::runtime_error("teacher CSR/compact-solver disagreement");}
 std::cerr<<"audit_pass="<<audit.size()<<" rows="<<rows<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
