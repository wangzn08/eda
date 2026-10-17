#pragma once
// Compute the finite short-distance kernel from architecture at initialization.
// Geometry/source rows have adjacent target cores for terminal scans.
#include "architecture_data.hpp"
#include <array>
#include <algorithm>
#include <cstdint>
#include <cmath>
#include <cstring>
#include <ctime>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <sys/mman.h>
#include <unistd.h>
#include "runtime_memory.hpp"
#ifndef RUNTIME_GEOMETRY_LOWER_BOUNDS
#define RUNTIME_GEOMETRY_LOWER_BOUNDS 0
#endif
class RuntimeShortKernel{
 struct Edge{int to,dx,dy,cost;};
 unsigned char*storage=nullptr;size_t mapping_bytes=0,packed_bytes=0;unsigned sources=0,bits=0;int minimum=0;std::vector<int>anchors;std::vector<int16_t>xs;std::vector<int16_t>lower_bounds;
 static size_t aligned(size_t n){size_t page=size_t(sysconf(_SC_PAGESIZE));return (n+page-1)/page*page;}
public:
 RuntimeShortKernel(const RuntimeShortKernel&)=delete;RuntimeShortKernel&operator=(const RuntimeShortKernel&)=delete;
 ~RuntimeShortKernel(){if(storage)munmap(storage,mapping_bytes);}
 RuntimeShortKernel(std::vector<int>samples,unsigned source_count=160,int radius_y=132,const std::string&reference=""):sources(source_count),anchors(std::move(samples)){
  if(!sources||sources>160||anchors.empty()||!std::is_sorted(anchors.begin(),anchors.end())||anchors.front()<1||anchors.back()>9||radius_y<95)throw std::runtime_error("Runtime kernel configuration");
  for(int x=-29;x<=29;++x)xs.push_back(x);for(int sign:{-1,1})for(int a:anchors)for(int r=0;r<10;++r)xs.push_back(sign*(20+a*10+r));
  size_t count=size_t(xs.size())*191*sources*160;if(RUNTIME_GEOMETRY_LOWER_BOUNDS)lower_bounds.resize(count/160);mapping_bytes=aligned(count*2+32);storage=static_cast<unsigned char*>(mmap(nullptr,mapping_bytes,PROT_READ|PROT_WRITE,MAP_ANON|MAP_PRIVATE,-1,0));if(storage==MAP_FAILED){storage=nullptr;throw std::runtime_error("Runtime kernel allocation");}auto*field=reinterpret_cast<int16_t*>(storage);
  auto start=std::clock();int maximum=INT32_MIN;minimum=INT32_MAX;uint64_t checked=0;
  try{
   {
    std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);unsigned n=0;for(unsigned i=0;i<std::size(archdata::NETS);++i){auto e=archdata::NETS[i];index[e.to]=n++;netout[e.from]=i;}if(n!=160)throw std::runtime_error("Core count");std::array<std::vector<Edge>,160>edges;
    for(auto a:archdata::ARCS)if(index[a.from]>=0&&netout[a.to]>=0){auto e=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[e.vector];edges[index[a.from]].push_back({index[e.to],v.x,v.y,a.delay+e.delay});}
    // The full reference certified all wanted distances <=3094. Nonnegative
    // edge costs permit a3100 cutoff; circular Dial buckets retain only the
    // live cost frontier instead of allocations from every settled cost.
    constexpr int RX=156,WX=313,limit=3100;unsigned bucket_count=1;for(const auto&list:edges)for(auto e:list){if(e.cost<0)throw std::runtime_error("Negative kernel edge");bucket_count=std::max(bucket_count,unsigned(e.cost)+1);}int wy=radius_y*2+1;auto state=[&](int x,int y,int p){return ((x+RX)*wy+y+radius_y)*160+p;};std::vector<uint16_t>d(size_t(WX)*wy*160);std::vector<std::vector<uint32_t>>buckets(bucket_count);
    std::ifstream proof;std::vector<int16_t>reference_values;if(!reference.empty()){proof.open(reference,std::ios::binary);std::array<char,416>h;proof.read(h.data(),h.size());uint32_t shape[6]={160,160,239,24,46,2};if(!proof||std::memcmp(h.data(),"FDCRAW01",8)||std::memcmp(h.data()+8,archdata::HASH,64)||std::memcmp(h.data()+392,shape,24))throw std::runtime_error("Reference header");reference_values.resize(size_t(160)*239*24*46);}
    for(unsigned s=0;s<sources;++s){std::fill(d.begin(),d.end(),65535);for(auto&b:buckets)b.clear();d[state(0,0,s)]=0;buckets[0].push_back(state(0,0,s));
     for(int cost=0;cost<limit;++cost){auto&bucket=buckets[cost%bucket_count];for(size_t j=0;j<bucket.size();++j){uint32_t u=bucket[j];if(d[u]!=cost)continue;int x=int(u/160)/wy-RX,y=int(u/160)%wy-radius_y;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx<-RX||nx>RX||ny<-radius_y||ny>radius_y||value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value%bucket_count].push_back(v);}}}bucket.clear();}
     if(proof.is_open()){proof.read(reinterpret_cast<char*>(reference_values.data()),reference_values.size()*2);if(!proof)throw std::runtime_error("Reference source");}
     for(unsigned xi=0;xi<xs.size();++xi){int x=xs[xi],ax=std::abs(x),qx=ax>29?(ax-20)/10:0;for(int y=-95;y<=95;++y){int ay=std::abs(y),q=ay/12,phase=(y>0?12:0)+ay%12,slope=y>0?127:125;const auto*row=d.data()+state(x,y,0);size_t destination=((size_t(xi)*191+y+95)*sources+s)*160;int smallest=INT16_MAX;
       for(unsigned t=0;t<160;++t){if(row[t]==65535)throw std::runtime_error("Short kernel unreachable");int value=int(row[t])-125*qx-q*slope;if(value<INT16_MIN||value>INT16_MAX)throw std::runtime_error("Short kernel scalar range");minimum=std::min(minimum,value);maximum=std::max(maximum,value);if(RUNTIME_GEOMETRY_LOWER_BOUNDS)smallest=std::min(smallest,value);field[destination+t]=int16_t(value);
        if(proof.is_open()){int expected=reference_values[((size_t(t)*239+x+119)*24+phase)*46+q];if(value!=expected)throw std::runtime_error("Short finite window differs from full reference at source="+std::to_string(s)+" x="+std::to_string(x)+" y="+std::to_string(y)+" end="+std::to_string(t));++checked;}
       }if(RUNTIME_GEOMETRY_LOWER_BOUNDS)lower_bounds[destination/160]=int16_t(smallest);
      }}
     if(s%8==7||s+1==sources)std::cerr<<"short_source="<<s<<" generation_cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';
    }
   }
   unsigned range=maximum-minimum;bits=1;while((uint32_t(1)<<bits)<=range)++bits;if(bits>16)throw std::runtime_error("Short packed range");size_t write=0;uint64_t buffer=0;unsigned pending=0;
   for(size_t i=0;i<count;++i){unsigned value=int(field[i])-minimum;buffer|=uint64_t(value)<<pending;pending+=bits;while(pending>=8){storage[write++]=uint8_t(buffer);buffer>>=8;pending-=8;}}if(pending)storage[write++]=uint8_t(buffer);packed_bytes=write;std::memset(storage+write,0,8);size_t keep=aligned(write+8);if(keep<mapping_bytes&&munmap(storage+keep,mapping_bytes-keep))throw std::runtime_error("Short kernel shrink");mapping_bytes=keep;
   release_unused_heap_pages();runtime_memory_checkpoint("short-packed");std::cerr<<"short_entries="<<count<<" min="<<minimum<<" max="<<maximum<<" bits="<<bits<<" packed_bytes="<<packed_bytes<<" checked="<<checked<<" init_cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';
  }catch(...){munmap(storage,mapping_bytes);storage=nullptr;throw;}
 }
 struct View{
  const unsigned char*lo=nullptr,*hi=nullptr;int minimum=0,slope=0,wl=0,wh=0,denominator=1,lower_lo=0,lower_hi=0;
  static unsigned raw(const unsigned char*p,unsigned target){unsigned bit=target*11;uint32_t v;std::memcpy(&v,p+(bit>>3),4);return (v>>(bit&7))&2047;}
  int get(unsigned target)const{int a=int(raw(lo,target))+minimum;if(!hi)return a+slope;int b=int(raw(hi,target))+minimum;return int(std::nearbyint(double(a*wl+b*wh)/denominator))+slope;}
  int lower_bound()const{if(!RUNTIME_GEOMETRY_LOWER_BOUNDS)throw std::runtime_error("Geometry bounds disabled");return (!hi?lower_lo:int(std::nearbyint(double(lower_lo*wl+lower_hi*wh)/denominator)))+slope;}
  void prefetch()const{for(unsigned j=0;j<220;j+=64){__builtin_prefetch(lo+j);if(hi)__builtin_prefetch(hi+j);}}
 };
 View view(unsigned source,int dx,int dy)const{if(bits!=11||source>=sources||std::abs(dx)>119||std::abs(dy)>95)throw std::runtime_error("Short prepared view");View v;v.minimum=minimum;int ax=std::abs(dx),qx=ax>29?(ax-20)/10:0;v.slope=qx*125+std::abs(dy)/12*(dy>0?127:125);auto row=[&](unsigned x,bool high){size_t i=(size_t(x)*191+dy+95)*sources+source;if(high){v.hi=storage+i*220;if(RUNTIME_GEOMETRY_LOWER_BOUNDS)v.lower_hi=lower_bounds[i];}else{v.lo=storage+i*220;if(RUNTIME_GEOMETRY_LOWER_BOUNDS)v.lower_lo=lower_bounds[i];}};if(!qx){row(dx+29,false);return v;}unsigned lo=0,hi=anchors.size()-1;for(unsigned k=0;k<anchors.size();++k){if(anchors[k]<=qx)lo=k;if(anchors[k]>=qx){hi=k;break;}}if(qx>=anchors.back())lo=hi=anchors.size()-1;unsigned offset=59+(dx>0?anchors.size()*10:0)+ax%10;row(offset+lo*10,false);if(lo!=hi){row(offset+hi*10,true);v.wl=anchors[hi]-qx;v.wh=qx-anchors[lo];v.denominator=anchors[hi]-anchors[lo];}return v;}
 int residual(unsigned source,unsigned target,unsigned x_index,int dy)const{if(source>=sources||target>=160||x_index>=xs.size()||std::abs(dy)>95)throw std::runtime_error("Short query");size_t i=((size_t(x_index)*191+dy+95)*sources+source)*160+target,bit=i*bits;uint32_t word;std::memcpy(&word,storage+(bit>>3),4);return int((word>>(bit&7))&((1u<<bits)-1))+minimum;}
 int cost(unsigned source,unsigned target,int dx,int dy)const{if(std::abs(dx)>119||std::abs(dy)>95)throw std::runtime_error("Short geometry");int ax=std::abs(dx),ay=std::abs(dy),qx=ax>29?(ax-20)/10:0,qy=ay/12,value;if(!qx)value=residual(source,target,dx+29,dy);else{unsigned lo=0,hi=anchors.size()-1;for(unsigned k=0;k<anchors.size();++k){if(anchors[k]<=qx)lo=k;if(anchors[k]>=qx){hi=k;break;}}if(qx>=anchors.back())lo=hi=anchors.size()-1;unsigned offset=59+(dx>0?anchors.size()*10:0)+ax%10;int l=residual(source,target,offset+lo*10,dy);value=lo==hi?l:int(std::nearbyint(double(l*(anchors[hi]-qx)+residual(source,target,offset+hi*10,dy)*(qx-anchors[lo]))/(anchors[hi]-anchors[lo])));}return value+125*qx+qy*(dy>0?127:125);}
 void save(const std::string&path)const{std::ofstream f(path,std::ios::binary);f.write("RTSHORT1",8);f.write(archdata::HASH,64);uint32_t h[6]={sources,160,uint32_t(xs.size()),191,bits,uint32_t(minimum)};f.write(reinterpret_cast<char*>(h),24);f.write(reinterpret_cast<const char*>(xs.data()),xs.size()*2);f.write(reinterpret_cast<const char*>(storage),packed_bytes);if(!f)throw std::runtime_error("Short research output");}
 size_t bytes()const{return packed_bytes;}
};
