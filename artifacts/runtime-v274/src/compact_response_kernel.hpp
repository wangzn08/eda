#pragma once
// Lossless finite response representation. Each geometry/source row has
// adjacent target descriptors. A descriptor returns its exact plateau value
// directly; only periods before the plateau access the shared curve dictionary.
#include "routing_search.hpp"
#include "xz_decode.hpp"
#include <fstream>
#include <cstring>
#include "runtime_memory.hpp"
#ifndef RUNTIME_GEOMETRY_LOWER_BOUNDS
#define RUNTIME_GEOMETRY_LOWER_BOUNDS 0
#endif
class CompactResponseKernel{
 unsigned nx=0,periods=0,used_periods=0;bool far=false;std::vector<unsigned>anchors;
 std::vector<uint32_t>fast,prefix;std::vector<unsigned char>slow;std::vector<int16_t>patterns,lower_bounds;
 static constexpr uint32_t id_mask=(1u<<20)-1;
 int residual(unsigned source,unsigned target,unsigned x,unsigned phase,unsigned q)const{
  size_t row=(size_t(x)*24+phase)*160+source;uint32_t d=fast[row*160+target];int tail=int16_t(d&65535);unsigned first=(d>>16)&63;if(q>=first)return tail;size_t p=size_t(prefix[row]+((d>>22)&255))*3;uint32_t id;std::memcpy(&id,slow.data()+p,4);id&=0xffffff;return tail+int(patterns[size_t(id)*periods+q-8])-patterns[size_t(id)*periods+used_periods-1];
 }
public:
 explicit CompactResponseKernel(const std::string&path){
  std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated response asset");};char magic[8],hash[64];std::array<uint16_t,160>ports;read(magic,8);read(hash,64);read(ports.data(),320);if(std::string(hash,64)!=archdata::HASH)throw std::runtime_error("Response hash");for(unsigned i=0;i<160;++i)if(ports[i]!=archdata::NETS[i].to)throw std::runtime_error("Response port order");unsigned np,width,flags;
  if(std::string(magic,8)=="CVNEAR02"){uint32_t shape[6];read(shape,24);uint32_t expected[6]={160,160,59,24,40,8};if(std::memcmp(shape,expected,24))throw std::runtime_error("Near response shape");nx=59;periods=40;read(&np,4);read(&width,4);read(&flags,4);}
  else if(std::string(magic,8)=="FARABS01"){far=true;uint32_t shape[8];read(shape,32);if(shape[0]!=160||shape[1]!=160||shape[3]!=24||shape[4]!=8||shape[5]!=38||shape[7]!=4)throw std::runtime_error("Far response shape");nx=shape[2];periods=38;np=shape[6];width=3;unsigned n;read(&n,4);if(!n||n>9||nx!=n*20)throw std::runtime_error("Far anchors");anchors.resize(n);read(anchors.data(),n*4);std::vector<int16_t>xs(nx);read(xs.data(),nx*2);unsigned i=0;for(int sign:{-1,1})for(unsigned a:anchors)for(int r=0;r<10;++r)if(xs[i++]!=sign*int(20+a*10+r))throw std::runtime_error("Far horizontal order");read(&flags,4);}
  else throw std::runtime_error("Response asset magic");
  if(np>id_mask||!np||width!=3||flags!=15)throw std::runtime_error("Response encoding");used_periods=std::min(periods,38u);size_t count=size_t(160)*160*nx*24;fast.resize(count);patterns.resize(size_t(np)*periods);
  {
   auto stream=read_remaining_asset(f);size_t bytes=count*2+patterns.size()*2+count*3;MappedBytes decoded(bytes);if(!decode_xz_exact(stream.data(),stream.size(),decoded.data(),bytes))throw std::runtime_error("Response XZ");std::memcpy(patterns.data(),decoded.data()+count*2,patterns.size()*2);const auto*code=decoded.data()+count*2+patterns.size()*2;
   for(unsigned t=0;t<160;++t)for(unsigned x=0;x<nx;++x)for(unsigned y=0;y<24;++y){int16_t previous=0;for(unsigned s=0;s<160;++s){size_t i=(((size_t(t)*nx+x)*24+y)*160+s);uint32_t id=code[i]|(uint32_t(code[count+i])<<8)|(uint32_t(code[count*2+i])<<16);uint16_t delta=uint16_t(decoded.data()[i])|(uint16_t(decoded.data()[count+i])<<8);int16_t offset=int16_t(uint16_t(delta+uint16_t(s?previous:0)));previous=offset;if(id>=np||offset<-2048||offset>2047)throw std::runtime_error("Response cell");size_t out=(((size_t(x)*24+y)*160+s)*160+t);fast[out]=id|(uint32_t(int(offset)+2048)<<20);}}
  }
  std::vector<unsigned char>first(np);for(unsigned p=0;p<np;++p){unsigned q=used_periods-1;const auto*v=patterns.data()+size_t(p)*periods;while(q&&v[q-1]==v[used_periods-1])--q;first[p]=q+8;}
  prefix.resize(count/160);if(RUNTIME_GEOMETRY_LOWER_BOUNDS)lower_bounds.resize(prefix.size()*used_periods);slow.reserve(count*3+4);
  for(size_t row=0;row<prefix.size();++row){prefix[row]=slow.size()/3;unsigned local=0;std::array<int,38>early,event;if(RUNTIME_GEOMETRY_LOWER_BOUNDS){early.fill(INT16_MAX);event.fill(INT16_MAX);}for(unsigned t=0;t<160;++t){uint32_t old=fast[row*160+t],id=old&id_mask;int offset=int(old>>20)-2048;const auto*p=patterns.data()+size_t(id)*periods;int tail=offset+p[used_periods-1];if(tail<INT16_MIN||tail>INT16_MAX)throw std::runtime_error("Response tail");if(RUNTIME_GEOMETRY_LOWER_BOUNDS){unsigned first_period=first[id]-8;event[first_period]=std::min(event[first_period],tail);for(unsigned q=0;q<first_period;++q)early[q]=std::min(early[q],offset+int(p[q]));}unsigned slot=0;if(first[id]>8){slot=local++;slow.push_back(id);slow.push_back(id>>8);slow.push_back(id>>16);}fast[row*160+t]=uint16_t(int16_t(tail))|(uint32_t(first[id])<<16)|(uint32_t(slot)<<22);}if(RUNTIME_GEOMETRY_LOWER_BOUNDS){int constant=INT16_MAX;for(unsigned q=0;q<used_periods;++q){constant=std::min(constant,event[q]);lower_bounds[row*used_periods+q]=int16_t(std::min(constant,early[q]));}}}
  slow.resize(slow.size()+4,0);release_unused_heap_pages();runtime_memory_checkpoint(far?"far-response":"near-response");std::cerr<<"response_kernel="<<(far?"far":"near")<<" descriptors="<<fast.size()<<" slow_bytes="<<slow.size()<<" patterns="<<np<<'\n';
 }
 bool is_far()const{return far;}
 const std::vector<unsigned>&horizontal_anchors()const{return anchors;}
 struct View{
  const CompactResponseKernel*model=nullptr;const uint32_t*lo=nullptr,*hi=nullptr;uint32_t prefix_lo=0,prefix_hi=0;unsigned q=0;int slope=0,wl=0,wh=0,denominator=1,lower_lo=0,lower_hi=0;
  int one(const uint32_t*row,uint32_t start,unsigned target)const{uint32_t d=row[target];int tail=int16_t(d&65535);if(q>=((d>>16)&63))return tail;size_t offset=size_t(start+((d>>22)&255))*3;uint32_t id;std::memcpy(&id,model->slow.data()+offset,4);const auto*p=model->patterns.data()+size_t(id&0xffffff)*model->periods;return tail+int(p[q-8])-p[model->used_periods-1];}
  int get(unsigned target)const{int a=one(lo,prefix_lo,target);if(!hi)return a+slope;return int(std::nearbyint(double(a*wl+one(hi,prefix_hi,target)*wh)/denominator))+slope;}
  int lower_bound()const{if(!RUNTIME_GEOMETRY_LOWER_BOUNDS)throw std::runtime_error("Geometry bounds disabled");return (!hi?lower_lo:int(std::nearbyint(double(lower_lo*wl+lower_hi*wh)/denominator)))+slope;}
  void prefetch_target(unsigned target)const{__builtin_prefetch(lo+target);if(hi)__builtin_prefetch(hi+target);}
  void prefetch()const{for(unsigned j=0;j<160;j+=16){__builtin_prefetch(lo+j);if(hi)__builtin_prefetch(hi+j);}}
 };
 View view(unsigned source,int dx,int dy)const{View v;v.model=this;int ax=std::abs(dx),ay=std::abs(dy);unsigned phase=(dy>0?12:0)+ay%12;v.q=ay/12;v.slope=int(v.q)*(dy>0?127:125);auto row=[&](unsigned x,bool high){size_t i=(size_t(x)*24+phase)*160+source;if(high){v.hi=fast.data()+i*160;v.prefix_hi=prefix[i];if(RUNTIME_GEOMETRY_LOWER_BOUNDS)v.lower_hi=lower_bounds[i*used_periods+v.q-8];}else{v.lo=fast.data()+i*160;v.prefix_lo=prefix[i];if(RUNTIME_GEOMETRY_LOWER_BOUNDS)v.lower_lo=lower_bounds[i*used_periods+v.q-8];}};if(!far){row(dx+29,false);return v;}int qx=(ax-20)/10;v.slope+=125*qx;unsigned lo=0,hi=anchors.size()-1;for(unsigned k=0;k<anchors.size();++k){if(int(anchors[k])<=qx)lo=k;if(int(anchors[k])>=qx){hi=k;break;}}if(qx>=int(anchors.back()))lo=hi=anchors.size()-1;unsigned offset=(dx>0?anchors.size()*10:0)+ax%10;row(offset+lo*10,false);if(lo!=hi){row(offset+hi*10,true);v.wl=anchors[hi]-qx;v.wh=qx-anchors[lo];v.denominator=anchors[hi]-anchors[lo];}return v;}
 int cost(unsigned source,unsigned target,int dx,int dy)const{
  int ax=std::abs(dx),ay=std::abs(dy);unsigned q=ay/12,phase=(dy>0?12:0)+ay%12;if(source>=160||target>=160||q<8||q>45||ax>119||(far?ax<=29:ax>29))throw std::runtime_error("Response query");int value;
  if(!far)value=residual(source,target,dx+29,phase,q);else{int qx=(ax-20)/10;unsigned lo=0,hi=anchors.size()-1;for(unsigned k=0;k<anchors.size();++k){if(int(anchors[k])<=qx)lo=k;if(int(anchors[k])>=qx){hi=k;break;}}if(qx>=int(anchors.back()))lo=hi=anchors.size()-1;unsigned offset=(dx>0?anchors.size()*10:0)+ax%10;int l=residual(source,target,offset+lo*10,phase,q);value=lo==hi?l:int(std::nearbyint(double(l*(int(anchors[hi])-qx)+residual(source,target,offset+hi*10,phase,q)*(qx-int(anchors[lo])))/(anchors[hi]-anchors[lo])));value+=qx*125;}return value+int(q)*(dy>0?127:125);
 }
 void prefetch(unsigned source,int dx,int dy)const{
  unsigned phase=(dy>0?12:0)+std::abs(dy)%12;auto row=[&](unsigned x){auto p=fast.data()+((size_t(x)*24+phase)*160+source)*160;for(unsigned j=0;j<160;j+=16)__builtin_prefetch(p+j);};if(!far){row(dx+29);return;}int ax=std::abs(dx),qx=(ax-20)/10;unsigned lo=0,hi=anchors.size()-1;for(unsigned k=0;k<anchors.size();++k){if(int(anchors[k])<=qx)lo=k;if(int(anchors[k])>=qx){hi=k;break;}}if(qx>=int(anchors.back()))lo=hi=anchors.size()-1;unsigned offset=(dx>0?anchors.size()*10:0)+ax%10;row(offset+lo*10);if(lo!=hi)row(offset+hi*10);
 }
};
