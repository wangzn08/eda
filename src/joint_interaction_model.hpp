#pragma once
#include "architecture_data.hpp"
#include "xz_decode.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <iterator>
#include <stdexcept>
#include <string>
#include <fstream>
#include <vector>
class JointInteractionModel{
 std::vector<int16_t>values;
public:
 explicit JointInteractionModel(const std::string&path,const std::array<uint16_t,160>&ports){
  std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated joint interaction");};
  char magic[8],hash[64];std::array<uint16_t,160>ids;uint64_t bytes;uint32_t qx,qy;unsigned char recipe[32];read(magic,8);read(hash,64);read(ids.data(),320);read(&bytes,8);read(&qx,4);read(&qy,4);read(recipe,32);
  if(std::string(magic,8)!="TRJXZ001" || std::string(hash,64)!=archdata::HASH || ids!=ports || bytes!=24576000 || qx!=5 || qy!=6)throw std::runtime_error("Invalid joint interaction header");
  const std::string expected="70ef07de45b1a045913cfac20cfe9cb84e97c5d70954dfe039f04d1d6b57e830",hex="0123456789abcdef";std::string actual;for(auto b:recipe){actual+=hex[b>>4];actual+=hex[b&15];}if(actual!=expected)throw std::runtime_error("Invalid joint baseline recipe");
  std::vector<unsigned char>stream((std::istreambuf_iterator<char>(f)),{});if(f.bad() || stream.empty() || stream.size()>100000000)throw std::runtime_error("Invalid joint stream");values.resize(bytes/2);if(!decode_xz_exact(stream.data(),stream.size(),reinterpret_cast<unsigned char*>(values.data()),bytes))throw std::runtime_error("Invalid joint XZ");
 }
 int raw_delta(unsigned s,unsigned t,int rx,int ry)const{
  unsigned ix=std::abs(rx)-20,iy=std::abs(ry)-24;return values[(((s*160+t)*4+(rx>0?2:0)+(ry>0?1:0))*10+ix)*12+iy];
 }
 int correction(unsigned s,unsigned t,int rx,int ry,int dx,int dy)const{
  unsigned ax=std::abs(dx),ay=std::abs(dy);if(ax<=29 || ay<=35)return 0;
  unsigned qx=(ax-20)/10,qy=(ay-24)/12,ix=std::abs(rx)-20,iy=std::abs(ry)-24;
  int delta=values[(((s*160+t)*4+(rx>0?2:0)+(ry>0?1:0))*10+ix)*12+iy];
  return delta*int(std::min(std::min(qx,5u)*6,std::min(qy,6u)*5))/30;
 }
};
