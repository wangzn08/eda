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
#include <climits>
#include <memory>
#include <type_traits>
#ifndef RUNTIME_REFINED_TERMINALS
#define RUNTIME_REFINED_TERMINALS 0
#endif
#ifndef RUNTIME_MASK_HOT_CODEC
#define RUNTIME_MASK_HOT_CODEC 0
#endif
#ifndef RUNTIME_MASK_DIRECT
#define RUNTIME_MASK_DIRECT 0
#endif
class ReservedTerminalCodes{
 std::unique_ptr<MappedBytes>memory;size_t count=0;
public:
 void reserve(size_t n){if(memory)throw std::runtime_error("Terminal reserve twice");memory=std::make_unique<MappedBytes>(n*2);}
 void resize(size_t n){if(!memory)reserve(n);if(memory->size()<n*2)throw std::runtime_error("Terminal reserve size");count=n;}
 size_t size()const{return count;}
 uint16_t*data(){return reinterpret_cast<uint16_t*>(memory->data());}const uint16_t*data()const{return reinterpret_cast<const uint16_t*>(memory->data());}
 uint16_t&operator[](size_t i){return data()[i];}uint16_t operator[](size_t i)const{return data()[i];}
 unsigned char*bytes(){return memory->data();}const unsigned char*bytes()const{return memory->data();}
};
class TerminalIntervalMaskCatalog{
 std::array<int,496>index{};std::array<uint32_t,496>required{};unsigned target_count=0;
 std::conditional_t<RUNTIME_MASK_DIRECT,ReservedTerminalCodes,std::vector<uint16_t>>codes;std::vector<std::vector<uint32_t>>palettes;std::vector<uint32_t>hot_palette;
 std::array<uint16_t,496>packed_offsets{};std::array<uint8_t,496>packed_widths{};unsigned packed_stride=0;
 static constexpr unsigned pivots[4]={0,40,80,120};
 static unsigned group(int x){return std::abs(x)<=29?x+29:59+(x>0?10:0)+std::abs(x)%10;}
 size_t offset(unsigned source,unsigned ti,int dx,int dy)const{unsigned phase=(dy>0?12:0)+std::abs(dy)%12,bin=std::abs(dy)>=96;return (((size_t(group(dx))*2+bin)*24+phase)*160+source)*target_count+ti;}
public:
 template<class Short,class Long,class Terminals>
 TerminalIntervalMaskCatalog(const Short&sh,const Long&near,const Long&far,const Terminals&terminal){
  static_assert(!(RUNTIME_MASK_DIRECT&&RUNTIME_MASK_HOT_CODEC));std::vector<unsigned>targets;index.fill(-1);for(unsigned t=0;t<496;++t)if(terminal[t].size()>1){index[t]=targets.size();targets.push_back(t);for(auto e:terminal[t])required[t]|=1u<<archdata::NETS[e.first].vector;packed_offsets[t]=packed_stride;packed_widths[t]=terminal[t].size()<=8?1:3;packed_stride+=packed_widths[t];}target_count=targets.size();if(RUNTIME_MASK_DIRECT){if(packed_stride<target_count*2)throw std::runtime_error("Terminal expansion stride");codes.reserve((size_t(79)*2*24*160*packed_stride+5)/2);}codes.resize(size_t(79)*2*24*160*target_count);palettes.resize(target_count);std::vector<MaskPaletteIndex>maps(target_count);
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
  if(RUNTIME_REFINED_TERMINALS)refine_exact(sh,near,far,terminal);
  if(RUNTIME_MASK_HOT_CODEC)encode_common_masks();
  if constexpr(RUNTIME_MASK_DIRECT)encode_direct_masks();
 }
 template<class Short,class Long,class Terminals>
 void refine_exact(const Short&sh,const Long&near,const Long&far,const Terminals&terminal){
  std::vector<unsigned>targets;for(unsigned t=0;t<496;++t)if(index[t]>=0)targets.push_back(t);
  std::vector<std::vector<uint32_t>>refined(target_count);std::vector<MaskPaletteIndex>maps(target_count);
  std::vector<uint32_t>candidate(size_t(160)*target_count),winner(candidate.size());std::vector<int16_t>cost(size_t(160)*160);
  std::array<std::array<uint64_t,33>,2>hist{};auto start=std::clock();
  for(unsigned g=0;g<79;++g){std::vector<int>xs;if(g<59)xs.push_back(int(g)-29);else for(int q=1;q<=9;++q)xs.push_back((g<69?-1:1)*(20+q*10+(g-59)%10));
   for(unsigned bin=0;bin<2;++bin)for(unsigned phase=0;phase<24;++phase){
    size_t block=((size_t(g)*2+bin)*24+phase)*160*target_count;
    for(unsigned s=0;s<160;++s)for(unsigned ti=0;ti<target_count;++ti){auto i=size_t(s)*target_count+ti;candidate[i]=palettes[ti][codes[block+i]];winner[i]=__builtin_popcount(candidate[i])==1?candidate[i]:0;}
    int sg=phase>=12?1:-1,ry=phase%12;
    for(int x:xs)for(unsigned q=bin?8:0;q<(bin?46:8);++q){int y=sg*int(q*12+ry);
     for(unsigned s=0;s<160;++s){if(!bin){auto v=sh.view(s,x,y);for(unsigned e=0;e<160;++e)cost[s*160+e]=v.get(e);}else{auto v=std::abs(x)<=29?near.view(s,x,y):far.view(s,x,y);for(unsigned e=0;e<160;++e)cost[s*160+e]=v.get(e);}}
     for(unsigned s=0;s<160;++s)for(unsigned ti=0;ti<target_count;++ti){auto i=size_t(s)*target_count+ti;uint32_t choices=candidate[i];if(winner[i]==choices)continue;int best=INT_MAX;unsigned selected=0;while(choices){unsigned ordinal=__builtin_ctz(choices);choices&=choices-1;auto e=terminal[targets[ti]][ordinal];int value=cost[s*160+e.first]+e.second;if(value<best){best=value;selected=ordinal;}}winner[i]|=1u<<selected;}
    }
    for(unsigned s=0;s<160;++s)for(unsigned ti=0;ti<target_count;++ti){auto i=size_t(s)*target_count+ti;uint32_t mask=winner[i];if(!mask||(mask&~candidate[i]))throw std::runtime_error("Refined terminal certificate");auto entry=maps[ti].intern(mask,refined[ti].size());if(entry.second){if(entry.first>=65536)throw std::runtime_error("Refined terminal palette width");refined[ti].push_back(mask);}codes[block+i]=entry.first;++hist[bin][__builtin_popcount(mask)];}
   }
   if(g%4==3||g==78)std::cerr<<"refined_mask_group="<<g+1<<"/79 cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';
  }
  palettes.swap(refined);refined.clear();maps.clear();release_unused_heap_pages();runtime_memory_checkpoint("terminal-interval-refined-catalog");
  for(unsigned bin=0;bin<2;++bin){uint64_t n=0,total=0;for(unsigned count=0;count<=32;++count){n+=hist[bin][count];total+=count*hist[bin][count];}std::cerr<<"refined_mask_bin="<<bin<<" mean_candidates="<<double(total)/n<<'\n';}
 }
 void encode_common_masks(){
  // Every subset of up to four ordinals in a24-terminal fan-in has a small
  // combinatorial rank. Share these frequent masks across all target ports;
  // retain an exact per-target escape palette for larger sets.
  unsigned choose[25][5]{};for(unsigned n=0;n<=24;++n){choose[n][0]=1;for(unsigned k=1;k<=4&&k<=n;++k)choose[n][k]=choose[n-1][k-1]+choose[n-1][k];}
  unsigned base[5]{};for(unsigned k=2;k<=4;++k)base[k]=base[k-1]+choose[24][k-1];hot_palette.resize(base[4]+choose[24][4]);
  auto rank=[&](uint32_t mask){unsigned k=__builtin_popcount(mask),j=0,result=base[k];while(mask){unsigned bit=__builtin_ctz(mask);mask&=mask-1;result+=choose[bit][++j];}return result;};
  std::vector<std::vector<uint16_t>>mapping(target_count);std::vector<std::vector<uint32_t>>cold(target_count);
  for(unsigned ti=0;ti<target_count;++ti){mapping[ti].resize(palettes[ti].size());for(unsigned i=0;i<palettes[ti].size();++i){uint32_t mask=palettes[ti][i];if(!(mask>>24)&&__builtin_popcount(mask)<=4){unsigned code=rank(mask);if(code>=hot_palette.size()||(hot_palette[code]&&hot_palette[code]!=mask))throw std::runtime_error("Terminal mask rank collision");hot_palette[code]=mask;mapping[ti][i]=code;}else{unsigned id=cold[ti].size();if(id>=32768)throw std::runtime_error("Cold terminal palette width");mapping[ti][i]=0x8000|id;cold[ti].push_back(mask);}}}
  uint64_t hot=0;for(size_t row=0;row<codes.size();row+=target_count)for(unsigned ti=0;ti<target_count;++ti){uint16_t code=mapping[ti][codes[row+ti]];codes[row+ti]=code;hot+=!(code&0x8000);}
  palettes.swap(cold);cold.clear();mapping.clear();release_unused_heap_pages();runtime_memory_checkpoint("terminal-shared-small-mask-codec");std::cerr<<"terminal_hot_mask_bytes="<<hot_palette.size()*4<<" fraction="<<double(hot)/codes.size()<<'\n';
 }
 void encode_direct_masks(){
  if constexpr(RUNTIME_MASK_DIRECT){std::vector<unsigned>targets;for(unsigned t=0;t<496;++t)if(index[t]>=0)targets.push_back(t);std::vector<uint16_t>row(target_count);size_t rows=codes.size()/target_count;auto*destination=reinterpret_cast<unsigned char*>(codes.data());
   // Expand backwards in the same mapping. Staging a complete16-bit row
   // protects it while variable-width mask bytes overwrite its old storage.
   for(size_t r=rows;r-->0;){std::memcpy(row.data(),codes.data()+r*target_count,target_count*2);for(unsigned ti=0;ti<target_count;++ti){unsigned t=targets[ti];uint32_t mask=palettes[ti][row[ti]];unsigned width=packed_widths[t];if(mask>>(width*8))throw std::runtime_error("Direct terminal mask width");std::memcpy(destination+r*packed_stride+packed_offsets[t],&mask,width);}}
   palettes.clear();palettes.shrink_to_fit();release_unused_heap_pages();runtime_memory_checkpoint("terminal-direct-packed-masks");std::cerr<<"terminal_direct_mask_bytes="<<rows*packed_stride<<" row_bytes="<<packed_stride<<'\n';
  }
 }
 size_t packed_offset(unsigned source,unsigned target,int dx,int dy)const{unsigned phase=(dy>0?12:0)+std::abs(dy)%12,bin=std::abs(dy)>=96;return (((size_t(group(dx))*2+bin)*24+phase)*160+source)*packed_stride+packed_offsets[target];}
 bool usable(unsigned target,uint32_t valid_vectors)const{return index[target]>=0&&(valid_vectors&required[target])==required[target];}
 uint32_t get(unsigned source,unsigned target,int dx,int dy)const{if constexpr(RUNTIME_MASK_DIRECT){auto*p=reinterpret_cast<const unsigned char*>(codes.data())+packed_offset(source,target,dx,dy);if(packed_widths[target]==1)return *p;uint32_t mask;std::memcpy(&mask,p,4);return mask&0xffffff;}else{unsigned ti=index[target];uint16_t code=codes[offset(source,ti,dx,dy)];if(RUNTIME_MASK_HOT_CODEC)return code&0x8000?palettes[ti][code&0x7fff]:hot_palette[code];return palettes[ti][code];}}
 void prefetch(unsigned source,unsigned target,int dx,int dy)const{if(index[target]>=0){if constexpr(RUNTIME_MASK_DIRECT)__builtin_prefetch(reinterpret_cast<const unsigned char*>(codes.data())+packed_offset(source,target,dx,dy));else __builtin_prefetch(codes.data()+offset(source,index[target],dx,dy));}}
};
