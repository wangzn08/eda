#pragma once
#include "routing_search.hpp"
#include "xz_decode.hpp"
#include <fstream>
#include <cstring>
#include <climits>

// Nearest-anchor shortest-path witness policy. Anchors are exact in a finite
// ideal graph; applying them at other distances/physical sites is approximate.
class IdealActionPolicy {
 struct Block{std::vector<unsigned char>data;size_t code_offset=0;unsigned width=0,patterns=0;};
 std::array<Block,20>blocks;
 std::array<uint8_t,239>xslot{};
 std::array<uint8_t,48>qslot{};
 uint32_t periods=0;
 size_t row_count=0;
public:
 explicit IdealActionPolicy(const std::string&path){
  std::ifstream f(path,std::ios::binary);char header[96]{};f.read(header,96);uint32_t shape[6];std::memcpy(shape,header+72,24);
  if(!f||std::memcmp(header,"IACTPOL2",8)||std::memcmp(header+8,archdata::HASH,64)||shape[0]!=160||shape[1]!=160||shape[2]!=119||shape[3]!=24||!shape[4]||shape[4]>48||shape[5]!=8)throw std::runtime_error("Ideal policy header");
  periods=shape[4];std::array<uint16_t,160>ports;f.read(reinterpret_cast<char*>(ports.data()),320);for(unsigned i=0;i<160;++i)if(ports[i]!=archdata::NETS[i].to)throw std::runtime_error("Ideal policy port order");
  std::array<int32_t,119>xs;f.read(reinterpret_cast<char*>(xs.data()),476);std::vector<uint32_t>qs(periods);f.read(reinterpret_cast<char*>(qs.data()),periods*4);uint32_t count;f.read(reinterpret_cast<char*>(&count),4);
  row_count=size_t(160)*119*24*periods;
  if(!f||count!=20)throw std::runtime_error("Ideal policy shape");
  for(int dx=-119;dx<=119;++dx){int best=INT_MAX;for(unsigned j=0;j<119;++j)if((std::abs(dx)<=29&&xs[j]==dx)||(std::abs(dx)>29&&(xs[j]>0)==(dx>0)&&std::abs(xs[j])%10==std::abs(dx)%10)){int distance=std::abs(dx-xs[j]);if(distance<best){best=distance;xslot[dx+119]=j;}}if(best==INT_MAX)throw std::runtime_error("Ideal policy x coverage");}
  for(unsigned q=0;q<48;++q){unsigned best=UINT_MAX;for(unsigned j=0;j<periods;++j){if(qs[j]>47)throw std::runtime_error("Ideal period knot");unsigned distance=std::abs(int(q)-int(qs[j]));if(distance<best){best=distance;qslot[q]=j;}}}
  for(auto&b:blocks){uint64_t bytes,encoded;f.read(reinterpret_cast<char*>(&b.patterns),4);f.read(reinterpret_cast<char*>(&b.width),4);f.read(reinterpret_cast<char*>(&bytes),8);f.read(reinterpret_cast<char*>(&encoded),8);b.code_offset=size_t(b.patterns)*8;
   if(!f||!b.patterns||b.patterns>16777216||(b.width!=2&&b.width!=3)||bytes!=b.code_offset+row_count*b.width||bytes>100000000||encoded>100000000)throw std::runtime_error("Ideal policy block");
   std::vector<unsigned char>stream(encoded);f.read(reinterpret_cast<char*>(stream.data()),encoded);b.data.resize(bytes+2);if(!f||!decode_xz_exact(stream.data(),stream.size(),b.data.data(),bytes))throw std::runtime_error("Ideal policy XZ");uint32_t previous=0,mask=b.width==2?65535:16777215;
   for(size_t row=0;row<row_count;++row){uint32_t id=0;auto p=b.data.data()+b.code_offset+row*b.width;std::memcpy(&id,p,b.width);if(row%periods)id=(id+previous)&mask;if(id>=b.patterns)throw std::runtime_error("Ideal policy code");std::memcpy(p,&id,b.width);previous=id;}
   for(size_t i=0;i<b.code_offset;++i)if(b.data[i]>=160&&b.data[i]!=255)throw std::runtime_error("Ideal policy action");
  }
  if(f.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Ideal policy trailing data");
 }
 unsigned select(unsigned source,unsigned target,int dx,int dy)const{
  if(source>=160||target>=160||std::abs(dx)>119||std::abs(dy)>=576)throw std::runtime_error("Ideal policy input");unsigned ay=std::abs(dy),phase=(dy>0?12:0)+ay%12;
  const auto&b=blocks[source/8];size_t row=((size_t(target)*119+xslot[dx+119])*24+phase)*periods+qslot[ay/12];uint32_t id=0;std::memcpy(&id,b.data.data()+b.code_offset+row*b.width,4);id&=b.width==2?65535:16777215;
  return b.data[size_t(id)*8+source%8];
 }
};
