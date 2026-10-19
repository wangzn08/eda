#pragma once
#include "routing_search.hpp"
#include "xz_decode.hpp"
#include <fstream>
#include <cstring>
#include "runtime_memory.hpp"
class CompactPhiModel{
 std::vector<int16_t>patterns;std::vector<unsigned char>codes;unsigned width=0;
public:
 explicit CompactPhiModel(const std::string&path){std::ifstream f(path,std::ios::binary);std::array<char,96>h;f.read(h.data(),h.size());uint32_t shape[6];std::memcpy(shape,h.data()+72,24);if(!f||std::memcmp(h.data(),"PHPATX01",8)||std::memcmp(h.data()+8,archdata::HASH,64)||shape[0]!=std::size(archdata::SITES)||shape[1]!=160||shape[2]!=24||shape[3]>16777216||(shape[4]!=2&&shape[4]!=3)||shape[5]!=1)throw std::runtime_error("Phi pattern header");width=shape[4];size_t n=std::size(archdata::SITES)*160;patterns.resize(size_t(shape[3])*24);codes.resize(n*width+4);{auto stream=read_remaining_asset(f);MappedBytes decoded(patterns.size()*2+n*width);if(!decode_xz_exact(stream.data(),stream.size(),decoded.data(),decoded.size()))throw std::runtime_error("Phi XZ");std::memcpy(patterns.data(),decoded.data(),patterns.size()*2);const auto*wire=decoded.data()+patterns.size()*2;for(size_t i=0;i<n;++i){uint32_t id=0;for(unsigned j=0;j<width;++j)id|=uint32_t(wire[size_t(j)*n+i])<<(8*j);if(id>=shape[3])throw std::runtime_error("Phi index");std::memcpy(codes.data()+i*width,&id,width);}}release_unused_heap_pages();runtime_memory_checkpoint("phi-patterns");}
 const int16_t*row(Node site,unsigned core)const{uint32_t id=0;std::memcpy(&id,codes.data()+(size_t(site)*160+core)*width,4);id&=width==2?65535:0xffffff;return patterns.data()+size_t(id)*24;}
 void prefetch_code(Node site,unsigned core)const{__builtin_prefetch(codes.data()+(size_t(site)*160+core)*width);}
 void prefetch_pattern(Node site,unsigned core)const{__builtin_prefetch(row(site,core));}
};
