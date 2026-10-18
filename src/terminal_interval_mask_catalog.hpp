#pragma once
// Reference-normalized interval certificates. For each endpoint, bound its
// cost DIFFERENCE to four common pivot endpoints over all periods/anchors.
// A terminal can be discarded only if its lower bound exceeds some other
// terminal's upper bound. Far-x interpolation expands differences by one unit
// to account for the difference of two nearest-even rounded interpolants.
#include "runtime_memory.hpp"
#include "mask_palette_index.hpp"
#include <unordered_map>
#include <array>
#include <vector>
#include <cstring>
#include <ctime>
class TerminalIntervalMaskCatalog{
 std::array<int,496>index{};std::array<uint32_t,496>required{};unsigned target_count=0;
 std::vector<uint16_t>codes;std::vector<std::vector<uint32_t>>palettes;
 static constexpr unsigned pivots[4]={0,40,80,120};
 static unsigned group(int x){return std::abs(x)<=29?x+29:59+(x>0?10:0)+std::abs(x)%10;}
 size_t offset(unsigned source,unsigned ti,int dx,int dy)const{unsigned phase=(dy>0?12:0)+std::abs(dy)%12,bin=std::abs(dy)>=96;return (((size_t(group(dx))*2+bin)*24+phase)*160+source)*target_count+ti;}
public:
 template<class Short,class Long,class Terminals>
 TerminalIntervalMaskCatalog(const Short&sh,const Long&near,const Long&far,const Terminals&terminal){
  std::vector<unsigned>targets;index.fill(-1);for(unsigned t=0;t<496;++t)if(terminal[t].size()>1){index[t]=targets.size();targets.push_back(t);for(auto e:terminal[t])required[t]|=1u<<archdata::NETS[e.first].vector;}target_count=targets.size();codes.resize(size_t(79)*2*24*160*target_count);palettes.resize(target_count);std::vector<MaskPaletteIndex>maps(target_count);
  std::vector<int16_t>lower(size_t(2)*4*160*160),upper(lower.size());std::array<int16_t,160>cost{};std::array<std::array<int16_t,160>,4>threshold;std::array<uint32_t,160>selected;std::array<std::array<uint64_t,33>,2>hist{};auto start=std::clock();
  for(unsigned g=0;g<79;++g){std::vector<int>xs;if(g<59)xs.push_back(int(g)-29);else for(int q:{1,3,6,9})xs.push_back((g<69?-1:1)*(20+q*10+(g-59)%10));int margin=g>=59?1:0;
   for(unsigned phase=0;phase<24;++phase){std::fill(lower.begin(),lower.end(),INT16_MAX);std::fill(upper.begin(),upper.end(),INT16_MIN);int sg=phase>=12?1:-1,ry=phase%12;
    for(int x:xs)for(unsigned q=0;q<46;++q){int y=sg*int(q*12+ry);unsigned bin=q>=8;
     for(unsigned s=0;s<160;++s){if(q<8){auto v=sh.view(s,x,y);for(unsigned e=0;e<160;++e)cost[e]=v.get(e);}else{auto v=std::abs(x)<=29?near.view(s,x,y):far.view(s,x,y);for(unsigned e=0;e<160;++e)cost[e]=v.get(e);}
      for(unsigned p=0;p<4;++p){int reference=cost[pivots[p]];size_t base=(size_t(bin)*4+p)*160*160+s;for(unsigned e=0;e<160;++e){int16_t difference=int16_t(int(cost[e])-reference);auto i=base+e*160;lower[i]=std::min(lower[i],difference);upper[i]=std::max(upper[i],difference);}}
     }
    }
    for(unsigned bin=0;bin<2;++bin)for(unsigned ti=0;ti<target_count;++ti){for(auto&row:threshold)row.fill(INT16_MAX);for(unsigned p=0;p<4;++p)for(auto e:terminal[targets[ti]]){const int16_t*u=upper.data()+(size_t(bin)*4+p)*160*160+e.first*160;for(unsigned s=0;s<160;++s)threshold[p][s]=std::min(threshold[p][s],int16_t(u[s]+e.second+margin));}
     selected.fill(0);unsigned ordinal=0;for(auto e:terminal[targets[ti]]){uint32_t bit=1u<<ordinal++;for(unsigned s=0;s<160;++s){bool possible=true;for(unsigned p=0;p<4;++p){int l=lower[(size_t(bin)*4+p)*160*160+e.first*160+s]+int(e.second)-margin;if(l>threshold[p][s]){possible=false;break;}}if(possible)selected[s]|=bit;}}
     for(unsigned s=0;s<160;++s){uint32_t mask=selected[s];if(!mask)throw std::runtime_error("Empty interval terminal mask");auto entry=maps[ti].intern(mask,palettes[ti].size());unsigned id=entry.first;if(entry.second){if(id>=65536)throw std::runtime_error("Interval terminal palette width");palettes[ti].push_back(mask);}codes[(((size_t(g)*2+bin)*24+phase)*160+s)*target_count+ti]=id;++hist[bin][__builtin_popcount(mask)];}
    }
   }
   if(g%4==3||g==78){size_t n=0;unsigned maximum=0;for(const auto&p:palettes){n+=p.size();maximum=std::max(maximum,unsigned(p.size()));}std::cerr<<"interval_mask_group="<<g+1<<"/79 palettes="<<n<<" max_per_target="<<maximum<<" cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';}
  }
  maps.clear();maps.shrink_to_fit();release_unused_heap_pages();runtime_memory_checkpoint("terminal-interval-mask-catalog");for(unsigned bin=0;bin<2;++bin){uint64_t count=0,total=0;for(unsigned n=0;n<=32;++n){count+=hist[bin][n];total+=n*hist[bin][n];}std::cerr<<"interval_mask_bin="<<bin<<" mean_candidates="<<double(total)/count<<'\n';}std::cerr<<"interval_mask_code_bytes="<<codes.size()*2<<'\n';
 }
 bool usable(unsigned target,uint32_t valid_vectors)const{return index[target]>=0&&(valid_vectors&required[target])==required[target];}
 uint32_t get(unsigned source,unsigned target,int dx,int dy)const{unsigned ti=index[target];return palettes[ti][codes[offset(source,ti,dx,dy)]];}
 void prefetch(unsigned source,unsigned target,int dx,int dy)const{if(index[target]>=0)__builtin_prefetch(codes.data()+offset(source,index[target],dx,dy));}
};
