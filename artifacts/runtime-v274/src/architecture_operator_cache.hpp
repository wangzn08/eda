#pragma once
#include "architecture_data.hpp"
#include <cstdint>
#include <vector>
#ifndef RUNTIME_OPERATOR_CACHE_BITS
#define RUNTIME_OPERATOR_CACHE_BITS 23
#endif
// Cache only the architecture terminal min-plus operator. The exact54-bit
// tag concatenates all geometry/mode fields with the16-bit vector legality.
// Final prediction, source entry, line fees and absolute pin pairs are absent.
class ArchitectureOperatorCache{
 struct __attribute__((packed)) Entry{uint64_t tag=0;uint32_t result=0;};static_assert(sizeof(Entry)==12);
 static constexpr unsigned capacity=size_t(1)<<RUNTIME_OPERATOR_CACHE_BITS,probes=8;
 mutable std::vector<Entry>entries;bool enabled=false;
 static uint64_t tag(uint64_t key,uint32_t vectors){return (key<<16)|vectors;}
 static size_t slot(uint64_t value){value^=value>>30;value*=0xbf58476d1ce4e5b9ull;value^=value>>27;value*=0x94d049bb133111ebull;value^=value>>31;return value&(capacity-1);}
public:
 explicit ArchitectureOperatorCache(bool active):enabled(active){static_assert(std::size(archdata::VECTORS)<=16);}
 void initialize(){if(enabled&&entries.empty())entries.resize(capacity);}
 static uint64_t key(unsigned source,unsigned target,int dx,int dy,bool cross,bool blocked){return (uint64_t(source)|(uint64_t(target)<<8)|(uint64_t(dx+119)<<17)|(uint64_t(dy+549)<<25)|(uint64_t(cross)<<36)|(uint64_t(blocked)<<37))+1;}
 void prefetch(uint64_t key,uint32_t vectors)const{size_t i=slot(tag(key,vectors));__builtin_prefetch(entries.data()+i);__builtin_prefetch(entries.data()+((i+6)&(capacity-1)));}
 bool get(uint64_t key,uint32_t vectors,uint32_t&result)const{uint64_t wanted=tag(key,vectors);size_t i=slot(wanted);for(unsigned n=0;n<probes;++n){auto e=entries[(i+n)&(capacity-1)];if(e.tag==wanted){result=e.result;return true;}if(!e.tag)return false;}return false;}
 void put(uint64_t key,uint32_t vectors,int nominal,unsigned end,unsigned arc,unsigned kind)const{if(nominal<0||nominal>=8192||end>=160||arc>=1024||(kind!=0&&kind!=2))return;uint64_t wanted=tag(key,vectors);size_t first=slot(wanted),i=first;for(unsigned n=0;n<probes;++n){i=(first+n)&(capacity-1);if(!entries[i].tag||entries[i].tag==wanted)break;if(n+1==probes)i=first;}entries[i]={wanted,unsigned(nominal)|(end<<13)|(arc<<21)|((kind==2?1u:0u)<<31)};}
 static int nominal(uint32_t word){return word&8191;}
 static unsigned end(uint32_t word){return (word>>13)&255;}
 static unsigned arc(uint32_t word){return (word>>21)&1023;}
 static unsigned kind(uint32_t word){return (word>>31)*2;}
 size_t bytes()const{return entries.size()*sizeof(Entry);}
};
