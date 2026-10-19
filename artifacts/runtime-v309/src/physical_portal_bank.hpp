#pragma once
#include "routing_search.hpp"
#include <fstream>
#include <cstring>
// Exact restricted-graph legs; a finite gateway subset is not an exact global oracle.
class PhysicalPortalBank {
 std::vector<uint16_t> data;
public:
 explicit PhysicalPortalBank(const std::string&path){std::ifstream f(path,std::ios::binary);char header[432];f.read(header,432);if(!f || std::memcmp(header,"PORTAL01",8) || std::memcmp(header+8,archdata::HASH,64))throw std::runtime_error("Physical portal header/hash");std::array<uint16_t,160>ports{};unsigned k=0;for(auto z:archdata::NETS)ports[k++]=z.to;if(k!=160||std::memcmp(header+72,ports.data(),320))throw std::runtime_error("Physical portal ports");uint32_t shape[6]={1,106,50,160,496,16};if(std::memcmp(header+392,shape,24))throw std::runtime_error("Physical portal shape");data.resize(size_t(106)*50*(160+496)*16);f.read(reinterpret_cast<char*>(data.data()),data.size()*2);if(!f||f.peek()!=EOF)throw std::runtime_error("Physical portal payload");}
 Distance cost(int core,int target,int ax,int ay,int bx,int by)const{if(core<0||core>=160||target<0||target>=496||ay<100||ay>=450||by<100||by>=450||ay/100!=by/100||ay%100>=50||by%100>=50||!(std::min(ax,bx)<76&&std::max(ax,bx)>89))return INF;auto pos=[](int x,int y){return size_t(x<76?x:x-14)*50+y%100;};auto a=&data[(pos(ax,ay)*160+core)*16];auto b=&data[size_t(106)*50*160*16+(pos(bx,by)*496+target)*16];Distance best=INF;for(unsigned h=0;h<16;++h)if(a[h]!=65535&&b[h]!=65535)best=std::min(best,Distance(a[h])+b[h]);return best;}
};
