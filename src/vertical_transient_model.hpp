#pragma once
#include "architecture_data.hpp"
#include <fstream>
#include <vector>
#include <cstring>
#include <zlib.h>
#include "xz_decode.hpp"
class VerticalTransientModel{
 std::vector<int16_t>values,far_delta;
 unsigned far_period=4;
 int at(unsigned s,unsigned t,int x,unsigned sign,unsigned band,unsigned r)const{return values[(((s*160+t)*59+x+29)*2+sign)*24+band*12+r];}
public:
 unsigned first_far_period()const{return far_period;}
 explicit VerticalTransientModel(const std::string&path,const std::array<uint16_t,160>&ports){std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated transient asset");};char magic[8],hash[64];std::array<uint16_t,160>ids;uint32_t transform;uint64_t bytes;read(magic,8);read(hash,64);read(ids.data(),320);read(&transform,4);read(&bytes,8);
 if((std::string(magic,8)!="TRVZL001" && std::string(magic,8)!="TRVXZ001") || std::string(hash,64)!=archdata::HASH || ids!=ports || transform>2 || bytes!=uint64_t(160)*160*59*48*2)throw std::runtime_error("Invalid transient header");
 std::vector<unsigned char>compressed((std::istreambuf_iterator<char>(f)),{});if(compressed.empty() || compressed.size()>100000000)throw std::runtime_error("Invalid transient stream");values.resize(bytes/2);if(std::string(magic,8)=="TRVXZ001"){if(!decode_xz_exact(compressed.data(),compressed.size(),reinterpret_cast<unsigned char*>(values.data()),bytes))throw std::runtime_error("Invalid transient XZ stream");}else{z_stream stream{};stream.next_in=compressed.data();stream.avail_in=compressed.size();stream.next_out=reinterpret_cast<Bytef*>(values.data());stream.avail_out=bytes;if(inflateInit(&stream)!=Z_OK)throw std::runtime_error("Transient inflate initialization failed");int result=inflate(&stream,Z_FINISH);bool valid=result==Z_STREAM_END && stream.total_out==bytes && stream.avail_in==0;inflateEnd(&stream);if(!valid)throw std::runtime_error("Invalid transient compressed stream");}
 for(unsigned pair=0;pair<160*160;++pair)for(unsigned x=0;x<59;++x)for(unsigned y=0;y<48;++y){size_t i=(pair*59+x)*48+y;int value=values[i];if(transform>=1 && x)value+=values[i-48];if(transform==2 && y)value+=values[i-1];if(transform==2 && x && y)value-=values[i-49];if(value < -32768 || value>32767)throw std::runtime_error("Transient inverse overflow");values[i]=value;}
 }
 void load_far_delta(const std::string&path,const std::array<uint16_t,160>&ports){
  std::ifstream f(path,std::ios::binary);char magic[8],hash[64];std::array<uint16_t,160>ids;uint32_t transform;uint64_t bytes;
  auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated far delta asset");};
  read(magic,8);read(hash,64);read(ids.data(),320);read(&transform,4);read(&bytes,8);
  if((std::string(magic,8)!="TRVFD001" && std::string(magic,8)!="TRVFD002") || std::string(hash,64)!=archdata::HASH || ids!=ports || transform!=0 || bytes!=uint64_t(160)*160*59*48*2)throw std::runtime_error("Invalid far delta header");
  if(std::string(magic,8)=="TRVFD002"){read(&far_period,4);if(far_period!=6)throw std::runtime_error("Invalid far first period");}
  std::vector<unsigned char>stream((std::istreambuf_iterator<char>(f)),{});if(f.bad() || stream.empty() || stream.size()>100000000)throw std::runtime_error("Invalid far delta payload");
  far_delta.resize(bytes/2);if(!decode_xz_exact(stream.data(),stream.size(),reinterpret_cast<unsigned char*>(far_delta.data()),bytes))throw std::runtime_error("Invalid far delta XZ");
 }
 int correction(unsigned s,unsigned t,int x,int dy,unsigned growth_cap)const{unsigned ay=std::abs(dy);if(ay<=35)return 0;unsigned q=(ay-24)/12,r=(ay-24)%12,sign=dy>0;int a=at(s,t,x,sign,0,r);if(q==1)return a;int b=at(s,t,x,sign,1,r);int slope=std::max(0,b-a);
  if(!far_delta.empty() && q>=3){
   size_t i=(((s*160+t)*59+x+29)*2+sign)*24+r;
   int f4=b+int(far_period-2)*slope+far_delta[i],f5=b+int(far_period-1)*slope+far_delta[i+12];
   if(q<far_period)return b+(f4-b)*int(q-2)/int(far_period-2);
   if(q==far_period)return f4;
   return f5+int(q-far_period-1)*std::max(0,f5-f4);
  }
  return b+int(std::min(q-2,growth_cap))*slope;}
};
