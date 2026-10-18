#pragma once
#include "routing_search.hpp"
#include "xz_decode.hpp"
#include <fstream>
#include <cstring>
#include <unordered_map>
#include "runtime_memory.hpp"
struct KernelBranch{Node site;uint16_t core;int32_t entry;};
struct KernelRequest{Node from=0,to=0;uint32_t mask=UINT32_MAX;unsigned count=0;int32_t local=1000000000;std::array<KernelBranch,32>branches;};
class InitialKernelCandidates{
 struct Entry{uint16_t vector,core;uint32_t cost;};std::array<std::vector<Entry>,496>entries;
 std::array<int,496>source_index{},target_index{};unsigned target_count=0;std::vector<uint16_t>mask_codes;std::vector<uint32_t>mask_values;std::vector<uint32_t>mask_starts;
public:
 std::array<int,496>core_index{};std::array<std::vector<std::pair<unsigned,unsigned>>,496>terminals;
 InitialKernelCandidates(const Graph&graph,const std::string&asset){core_index.fill(-1);source_index.fill(-1);target_index.fill(-1);for(unsigned i=0;i<160;++i){auto e=archdata::NETS[i];core_index[e.to]=i;terminals[e.to].push_back({i,0});}for(auto a:archdata::ARCS){if(core_index[a.from]>=0)terminals[a.to].push_back({unsigned(core_index[a.from]),unsigned(a.delay)});int ni=graph.net_out(a.to);if(ni>=0){auto n=archdata::NETS[ni];entries[a.from].push_back({uint16_t(n.vector),uint16_t(core_index[n.to]),uint32_t(a.delay+n.delay)});}}
  unsigned source_count=0;for(unsigned p=0;p<496;++p)if(core_index[p]<0&&graph.net_out(p)<0&&entries[p].size()>16){if(entries[p].size()>32)throw std::runtime_error("Source candidate size");source_index[p]=source_count++;}for(unsigned t=0;t<496;++t)if(!terminals[t].empty())target_index[t]=target_count++;
  size_t n=size_t(source_count)*target_count*1896;std::ifstream f(asset,std::ios::binary);std::array<char,84>h;f.read(h.data(),h.size());uint32_t count;uint64_t bytes;std::memcpy(&count,h.data()+72,4);std::memcpy(&bytes,h.data()+76,8);if(!f||std::memcmp(h.data(),"SRCMSK01",8)||std::memcmp(h.data()+8,archdata::HASH,64)||count!=8||bytes!=n*4)throw std::runtime_error("Source hint header");
  {auto wire=read_remaining_asset(f);MappedBytes raw(bytes);if(!decode_xz_exact(wire.data(),wire.size(),raw.data(),bytes))throw std::runtime_error("Source hint XZ");const auto*masks=reinterpret_cast<const uint32_t*>(raw.data());mask_codes.resize(n);mask_starts.resize(source_count);for(unsigned p=0;p<496;++p)if(source_index[p]>=0){unsigned si=source_index[p];mask_starts[si]=mask_values.size();std::unordered_map<uint32_t,uint16_t>map;map.reserve(32768);size_t begin=size_t(si)*target_count*1896,end=begin+size_t(target_count)*1896;for(size_t i=begin;i<end;++i){uint32_t mask=masks[i];if(__builtin_popcount(mask)!=8||(entries[p].size()<32&&(mask>>entries[p].size())))throw std::runtime_error("Source hint mask");auto it=map.find(mask);unsigned id;if(it==map.end()){id=map.size();if(id>=65536)throw std::runtime_error("Source catalogue range");map.emplace(mask,uint16_t(id));mask_values.push_back(mask);}else id=it->second;mask_codes[i]=id;}}}
  release_unused_heap_pages();runtime_memory_checkpoint("source-hints-local-catalog");

 }
 void prepare(const Graph&graph,Node from,Node to,KernelRequest&r,bool force_all=false)const{
  r.from=from;r.to=to;r.mask=UINT32_MAX;r.count=0;r.local=from==to?0:1000000000;Node site=from/496,target_site=to/496;unsigned port=from%496,target=to%496;auto a=archdata::SITES[site],b=archdata::SITES[target_site];
  if(site==target_site)for(auto e:graph.local_out(port))if(e.port==target)r.local=std::min(r.local,int32_t(e.delay));
  if(!force_all&&source_index[port]>=0&&target_index[target]>=0){int dx=b.x-a.x,dy=b.y-a.y;bool cross=std::min(a.x,b.x)<76&&std::max(a.x,b.x)>89;if(std::abs(dy)>35&&!cross){unsigned xp=std::abs(dx)<=29?dx+29:59+(dx<0?10:0)+std::abs(dx)%10,phase=xp*24+(dy<0?12:0)+std::abs(dy)%12;r.mask=mask_values[mask_starts[source_index[port]]+mask_codes[(size_t(source_index[port])*target_count+target_index[target])*1896+phase]];}}
  auto append=[&](Move m,unsigned core,unsigned entry){if(m.site!=NONE){if(r.count==32)throw std::runtime_error("Source request size");r.branches[r.count++]={m.site,uint16_t(core),int32_t(entry+m.delay)};}};
  if(core_index[port]>=0)r.branches[r.count++]={site,uint16_t(core_index[port]),0};else if(graph.net_out(port)>=0){unsigned n=graph.net_out(port);auto e=archdata::NETS[n];append(graph.net_move(site,n,false),core_index[e.to],e.delay);}else{unsigned i=0;for(auto e:entries[port]){if(r.mask==UINT32_MAX||(r.mask&(1u<<i)))append(graph.forward_vector_move(site,e.vector),e.core,e.cost);++i;}}
 }
};
