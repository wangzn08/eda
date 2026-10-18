#pragma once
// Compile terminal minima from architecture distance responses. On horizontal
// interpolation, a shared first minimizer at both anchors remains the first
// minimizer after nearest-even rounding. Other cases retain the full scan.
#include "runtime_memory.hpp"
#include <unordered_map>
#include <array>
#include <vector>
#include <cstring>
#include <iostream>
#include <ctime>
class TerminalChoiceCatalog{
public:
 using Profile=std::array<unsigned char,46>;
 struct Hash{size_t operator()(const Profile&p)const noexcept{uint64_t h=1469598103934665603ull;for(auto b:p){h^=b;h*=1099511628211ull;}return h;}};
 std::array<int,496>target_index{};std::vector<unsigned>targets;std::vector<int>xs;
 std::vector<std::vector<Profile>>profiles;std::vector<uint16_t>codes;
 template<class Short,class Long,class Terminals>
 TerminalChoiceCatalog(const Short&shorts,const Long&near,const Long&far,const Terminals&terminal,unsigned geometry_limit=0,unsigned first_q=0,unsigned last_q=46){
  target_index.fill(-1);for(unsigned t=0;t<496;++t)if(terminal[t].size()>1){target_index[t]=targets.size();targets.push_back(t);}for(int x=-29;x<=29;++x)xs.push_back(x);for(int sign:{-1,1})for(int a:{1,3,6,9})for(int r=0;r<10;++r)xs.push_back(sign*(20+10*a+r));
  size_t count=size_t(xs.size())*24*160*targets.size();if(!geometry_limit)codes.resize(count);profiles.resize(targets.size());std::vector<std::unordered_map<Profile,uint32_t,Hash>>dictionaries(targets.size());
  std::vector<int16_t>costs(160*160),best(160);std::vector<unsigned char>arg(160),winners(size_t(46)*targets.size()*160);auto start=std::clock();unsigned total=xs.size()*24,limit=geometry_limit?std::min(geometry_limit,total):total;
  for(unsigned sample=0;sample<limit;++sample){unsigned geometry=geometry_limit?sample*total/limit:sample,xi=geometry/24,phase=geometry%24;int x=xs[xi],sg=phase>=12?1:-1,ry=phase%12,qx=std::abs(x)>29?(std::abs(x)-20)/10:0;
   for(unsigned q=first_q;q<last_q;++q){int y=sg*int(q*12+ry),slope=125*qx+int(q)*(sg>0?127:125);
    for(unsigned s=0;s<160;++s){if(q<8){auto v=shorts.view(s,x,y);for(unsigned e=0;e<160;++e)costs[e*160+s]=int16_t(v.get(e)-slope);}else{auto v=std::abs(x)<=29?near.view(s,x,y):far.view(s,x,y);for(unsigned e=0;e<160;++e)costs[e*160+s]=int16_t(v.get(e)-slope);}}
    for(unsigned ti=0;ti<targets.size();++ti){std::fill(best.begin(),best.end(),INT16_MAX);std::fill(arg.begin(),arg.end(),0);unsigned ordinal=0;for(auto e:terminal[targets[ti]]){const int16_t*c=costs.data()+e.first*160;for(unsigned s=0;s<160;++s){int16_t value=int16_t(c[s]+e.second);if(value<best[s]){best[s]=value;arg[s]=ordinal;}}++ordinal;}std::memcpy(winners.data()+(size_t(q)*targets.size()+ti)*160,arg.data(),160);}
   }
   for(unsigned ti=0;ti<targets.size();++ti)for(unsigned s=0;s<160;++s){Profile p{};for(unsigned q=first_q;q<last_q;++q)p[q]=winners[(size_t(q)*targets.size()+ti)*160+s];auto&map=dictionaries[ti];auto it=map.find(p);unsigned id;if(it==map.end()){id=profiles[ti].size();if(!geometry_limit&&id>=65536)throw std::runtime_error("Terminal catalogue needs wider local IDs");profiles[ti].push_back(p);map.emplace(p,uint32_t(id));}else id=it->second;if(!geometry_limit)codes[(size_t(geometry)*160+s)*targets.size()+ti]=id;}
   if(sample%16==15||sample+1==limit){size_t n=0;unsigned maximum=0;for(const auto&p:profiles){n+=p.size();maximum=std::max(maximum,unsigned(p.size()));}std::cerr<<"terminal_geometry="<<sample+1<<'/'<<limit<<" profiles="<<n<<" max_per_target="<<maximum<<" cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';}
  }
  std::array<uint64_t,47>tail_hist{};for(const auto&list:profiles)for(const auto&p:list){unsigned first=45;while(first&&p[first-1]==p[45])--first;++tail_hist[first];}for(unsigned i=0;i<47;++i)if(tail_hist[i])std::cerr<<"terminal_tail_first="<<i<<" profiles="<<tail_hist[i]<<'\n';dictionaries.clear();dictionaries.shrink_to_fit();release_unused_heap_pages();runtime_memory_checkpoint("terminal-choices");size_t pattern_bytes=0;for(const auto&p:profiles)pattern_bytes+=p.size()*46;std::cerr<<"terminal_choice_code_bytes="<<codes.size()*2<<" profile_bytes="<<pattern_bytes<<'\n';
 }
};
