#pragma once
#include "architecture_data.hpp"
#include "xz_decode.hpp"
#include <algorithm>
#include <cmath>
#ifndef CORE_MULTI_ANCHOR
#define CORE_MULTI_ANCHOR 0
#endif
#include <array>
#include <cstdint>
#include <iterator>
#include <stdexcept>
#include <string>
#include <fstream>
#include <vector>
class JointInteractionModel{
 std::vector<int16_t>values;bool multi_anchor=false;
public:
 explicit JointInteractionModel(const std::string&path,const std::array<uint16_t,160>&ports){
  std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated joint interaction");};
  char magic[8],hash[64];std::array<uint16_t,160>ids;uint64_t bytes;uint32_t qx=0,qy=0;unsigned char recipe[32];read(magic,8);read(hash,64);read(ids.data(),320);
  bool transformed=std::string(magic,8)=="TRMXZ002";multi_anchor=std::string(magic,8)=="TRMXZ001" || transformed;
  if(multi_anchor){if(!CORE_MULTI_ANCHOR)throw std::runtime_error("Multi-anchor asset requires research-enabled runtime");uint32_t shape[2];int32_t xs[3],ys[3];read(shape,8);read(xs,12);read(ys,12);read(&bytes,8);if(shape[0]!=3||shape[1]!=3||xs[0]!=1||xs[1]!=2||xs[2]!=5||ys[0]!=1||ys[1]!=2||ys[2]!=6||bytes!=221184000)throw std::runtime_error("Invalid multi-anchor dimensions");}
  else{read(&bytes,8);read(&qx,4);read(&qy,4);if(std::string(magic,8)!="TRJXZ001"||bytes!=24576000||qx!=5||qy!=6)throw std::runtime_error("Invalid joint dimensions");}
  read(recipe,32);if(std::string(hash,64)!=archdata::HASH||ids!=ports)throw std::runtime_error("Invalid joint architecture");
  const std::string expected="70ef07de45b1a045913cfac20cfe9cb84e97c5d70954dfe039f04d1d6b57e830",hex="0123456789abcdef";std::string actual;for(auto b:recipe){actual+=hex[b>>4];actual+=hex[b&15];}if(actual!=expected)throw std::runtime_error("Invalid joint baseline recipe");
  std::vector<unsigned char>stream((std::istreambuf_iterator<char>(f)),{});if(f.bad() || stream.empty() || stream.size()>100000000)throw std::runtime_error("Invalid joint stream");values.resize(bytes/2);if(!decode_xz_exact(stream.data(),stream.size(),reinterpret_cast<unsigned char*>(values.data()),bytes))throw std::runtime_error("Invalid joint XZ");if(transformed){for(size_t pos=0;pos<values.size();pos+=9)for(unsigned x=0;x<3;++x)for(unsigned y=0;y<3;++y){int i=pos+x*3+y,v=values[i];if(x)v+=values[i-3];if(y)v+=values[i-1];if(x && y)v-=values[i-4];if(v<-32768 || v>32767)throw std::runtime_error("Multi-anchor inverse overflow");values[i]=int16_t(v);}}
 }
 bool multi()const{return CORE_MULTI_ANCHOR && multi_anchor;}
 int raw_delta(unsigned s,unsigned t,int rx,int ry)const{
  unsigned ix=std::abs(rx)-20,iy=std::abs(ry)-24;size_t pos=(((s*160+t)*4+(rx>0?2:0)+(ry>0?1:0))*10+ix)*12+iy;return values[multi()?pos*9+8:pos];
 }
 int correction(unsigned s,unsigned t,int rx,int ry,int dx,int dy)const{
  unsigned ax=std::abs(dx),ay=std::abs(dy);if(ax<=29 || ay<=35)return 0;
  unsigned qx=(ax-20)/10,qy=(ay-24)/12,ix=std::abs(rx)-20,iy=std::abs(ry)-24;
  if(multi()){const int xs[3]={1,2,5},ys[3]={1,2,6};int xx=std::min(qx,5u),yy=std::min(qy,6u),i=xx<=2?0:1,j=yy<=2?0:1,wx=xx-xs[i],wy=yy-ys[j],sx=xs[i+1]-xs[i],sy=ys[j+1]-ys[j];size_t pos=(((s*160+t)*4+(rx>0?2:0)+(ry>0?1:0))*10+ix)*12+iy;auto*c=values.data()+pos*9;int sum=(sx-wx)*(sy-wy)*c[i*3+j]+wx*(sy-wy)*c[(i+1)*3+j]+(sx-wx)*wy*c[i*3+j+1]+wx*wy*c[(i+1)*3+j+1];return int(std::nearbyint(double(sum)/(sx*sy)));}
  int delta=values[(((s*160+t)*4+(rx>0?2:0)+(ry>0?1:0))*10+ix)*12+iy];
  return delta*int(std::min(std::min(qx,5u)*6,std::min(qy,6u)*5))/30;
 }
};
