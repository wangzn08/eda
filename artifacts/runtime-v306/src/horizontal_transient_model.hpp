#pragma once
#include "architecture_data.hpp"
#include <fstream>
#include <vector>
#include <cstring>
#include <zlib.h>
#include "xz_decode.hpp"
#include "transient_dictionary_decode.hpp"
class HorizontalTransientModel{
 std::vector<int16_t>values;
 int at(unsigned s,unsigned t,int y,unsigned sign,unsigned band,unsigned r)const{return values[(((s*160+t)*71+y+35)*2+sign)*20+band*10+r];}
public:
 std::vector<int16_t> take_values(){return std::move(values);}
 explicit HorizontalTransientModel(const std::string&path,const std::array<uint16_t,160>&ports){std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated transient asset");};char magic[8],hash[64];std::array<uint16_t,160>ids;uint32_t transform;uint64_t bytes;read(magic,8);read(hash,64);read(ids.data(),320);read(&transform,4);read(&bytes,8);
 if((std::string(magic,8)!="TRHZL001" && std::string(magic,8)!="TRHXZ001" && std::string(magic,8)!="TRHDIC01") || std::string(hash,64)!=archdata::HASH || ids!=ports || transform>2 || bytes!=uint64_t(160)*160*71*40*2)throw std::runtime_error("Invalid transient header");
 std::vector<unsigned char>compressed((std::istreambuf_iterator<char>(f)),{});if(compressed.empty() || compressed.size()>100000000)throw std::runtime_error("Invalid transient stream");values.resize(bytes/2);if(std::string(magic,8)=="TRHDIC01"){if(transform!=0)throw std::runtime_error("Dictionary requires raw bands");decode_transient_dictionary(compressed,values.data(),bytes,10);}else if(std::string(magic,8)=="TRHXZ001"){if(!decode_xz_exact(compressed.data(),compressed.size(),reinterpret_cast<unsigned char*>(values.data()),bytes))throw std::runtime_error("Invalid transient XZ stream");}else{z_stream stream{};stream.next_in=compressed.data();stream.avail_in=compressed.size();stream.next_out=reinterpret_cast<Bytef*>(values.data());stream.avail_out=bytes;if(inflateInit(&stream)!=Z_OK)throw std::runtime_error("Transient inflate initialization failed");int result=inflate(&stream,Z_FINISH);bool valid=result==Z_STREAM_END && stream.total_out==bytes && stream.avail_in==0;inflateEnd(&stream);if(!valid)throw std::runtime_error("Invalid transient compressed stream");}
 for(unsigned pair=0;pair<160*160;++pair)for(unsigned x=0;x<71;++x)for(unsigned y=0;y<40;++y){size_t i=(pair*71+x)*40+y;int value=values[i];if(transform>=1 && x)value+=values[i-40];if(transform==2 && y)value+=values[i-1];if(transform==2 && x && y)value-=values[i-41];if(value < -32768 || value>32767)throw std::runtime_error("Transient inverse overflow");values[i]=value;}
 }
 int correction(unsigned s,unsigned t,int y,int dx,unsigned growth_cap)const{unsigned ax=std::abs(dx);if(ax<=29)return 0;unsigned q=(ax-20)/10,r=(ax-20)%10,sign=dx>0;int a=at(s,t,y,sign,0,r);if(q==1)return a;int b=at(s,t,y,sign,1,r);return b+int(std::min(q-2,growth_cap))*std::max(0,b-a);}
};
