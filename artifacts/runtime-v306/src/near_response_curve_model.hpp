#pragma once
#include "routing_search.hpp"
#include "xz_decode.hpp"
#include <fstream>
#include <cstring>
class NearResponseCurveModel {
 std::vector<unsigned char>cells;std::vector<int16_t>patterns;unsigned stride=0,pattern_count=0;uint32_t id_mask=0;bool phase_major=false;
public:
 explicit NearResponseCurveModel(const std::string&path){
  std::ifstream f(path,std::ios::binary);char h[424];f.read(h,sizeof h);
  bool transformed=!std::memcmp(h,"CVNEAR02",8);if(!f||(!transformed&&std::memcmp(h,"CVNEAR01",8))||std::memcmp(h+8,archdata::HASH,64))throw std::runtime_error("Curve header/hash");
  std::array<uint16_t,160>ports;unsigned k=0;for(auto net:archdata::NETS)ports[k++]=net.to;if(k!=160||std::memcmp(h+72,ports.data(),320))throw std::runtime_error("Curve ports");
  uint32_t shape[6]={160,160,59,24,40,8},width; if(std::memcmp(h+392,shape,24))throw std::runtime_error("Curve shape");std::memcpy(&pattern_count,h+416,4);std::memcpy(&width,h+420,4);
  uint32_t flags=0;if(transformed){f.read(reinterpret_cast<char*>(&flags),4);if(!f||flags>31||((flags&24)&&!(flags&1)))throw std::runtime_error("Curve layout flags");}phase_major=flags&1;
  if(!pattern_count||pattern_count>10000000||(width!=2&&width!=3&&width!=4)||(width==2&&pattern_count>65536)||(width==3&&pattern_count>16777216))throw std::runtime_error("Curve dictionary shape");
  constexpr size_t count=size_t(160)*160*59*24;size_t bytes=count*2+size_t(pattern_count)*40*2+count*width;
  std::vector<unsigned char>stream((std::istreambuf_iterator<char>(f)),{});if(f.bad()||stream.empty()||stream.size()>100000000)throw std::runtime_error("Curve stream");std::vector<unsigned char>decoded(bytes);
  if(!decode_xz_exact(stream.data(),stream.size(),decoded.data(),bytes))throw std::runtime_error("Curve XZ");
  patterns.resize(size_t(pattern_count)*40);std::memcpy(patterns.data(),decoded.data()+count*2,patterns.size()*2);
  stride=width+2;id_mask=width==4?UINT32_MAX:(uint32_t(1)<<(width*8))-1;cells.resize(count*stride+2);const auto*codes=decoded.data()+count*2+patterns.size()*2;
  for(size_t i=0;i<count;++i){uint32_t id=0;uint16_t offset=0;for(unsigned j=0;j<width;++j){unsigned char byte=codes[(flags&2)?size_t(j)*count+i:i*width+j];id|=uint32_t(byte)<<(j*8);}for(unsigned j=0;j<2;++j)offset|=uint16_t(decoded[(flags&4)?size_t(j)*count+i:i*2+j])<<(j*8);
   if(i%160){if(flags&16){uint32_t prior;std::memcpy(&prior,cells.data()+(i-1)*stride+2,4);id=(id+(prior&id_mask))&id_mask;}if(flags&8){uint16_t prior;std::memcpy(&prior,cells.data()+(i-1)*stride,2);offset=uint16_t(offset+prior);}}
   if(id>=pattern_count)throw std::runtime_error("Curve code index");std::memcpy(cells.data()+i*stride,&offset,2);std::memcpy(cells.data()+i*stride+2,&id,width);}
 }
 static bool supports(int dx,int dy){return std::abs(dx)<=29&&std::abs(dy)>=96&&std::abs(dy)<=575;}
 int cost(unsigned source,unsigned target,int dx,int dy)const{
  unsigned ay=std::abs(dy),q=ay/12,r=ay%12,phase=(dy>0?12:0)+r;size_t i=(phase_major?((size_t(target)*59+dx+29)*24+phase)*160+source:((size_t(source)*160+target)*59+dx+29)*24+phase)*stride;
  int16_t offset;uint32_t id=0;std::memcpy(&offset,cells.data()+i,2);std::memcpy(&id,cells.data()+i+2,4);id&=id_mask;
  return int(offset)+patterns[size_t(id)*40+q-8]+int(q)*(dy>0?127:125);
 }
};
