#pragma once
#include "routing_search.hpp"
#include <fstream>
#include <cstring>
#include "xz_decode.hpp"
class TransientTailPatch {
 std::vector<int16_t>values;
public:
 explicit TransientTailPatch(const std::string&path){std::ifstream f(path,std::ios::binary);char h[428];f.read(h,sizeof h);if(!f||(std::memcmp(h,"TAILRAW1",8)&&std::memcmp(h,"TAILXZ01",8))||std::memcmp(h+8,archdata::HASH,64))throw std::runtime_error("Tail header/hash");std::array<uint16_t,160>ports;unsigned k=0;for(auto n:archdata::NETS)ports[k++]=n.to;if(k!=160||std::memcmp(h+72,ports.data(),320))throw std::runtime_error("Tail ports");uint32_t shape[5]={160,160,59,24,4};int32_t knots[4]={12,20,32,42};if(std::memcmp(h+392,shape,20)||std::memcmp(h+412,knots,16))throw std::runtime_error("Tail shape/knots");values.resize(size_t(160)*160*59*24*4);if(!std::memcmp(h,"TAILRAW1",8)){f.read(reinterpret_cast<char*>(values.data()),values.size()*2);if(!f||f.peek()!=EOF)throw std::runtime_error("Tail payload");}else{std::vector<unsigned char>c((std::istreambuf_iterator<char>(f)),{});if(f.bad()||c.empty()||c.size()>100000000||!decode_xz_exact(c.data(),c.size(),reinterpret_cast<unsigned char*>(values.data()),values.size()*2))throw std::runtime_error("Tail XZ payload");auto add=[&](size_t i,size_t prior){uint16_t v=uint16_t(int(values[i])+int(values[prior]));std::memcpy(&values[i],&v,2);};for(size_t pair=0;pair<25600;++pair){size_t off=pair*59*24*4;for(unsigned x=1;x<59;++x)for(unsigned yr=0;yr<96;++yr)add(off+x*96+yr,off+(x-1)*96+yr);for(unsigned x=0;x<59;++x)for(unsigned y=1;y<24;++y)for(unsigned k=0;k<4;++k)add(off+x*96+y*4+k,off+x*96+(y-1)*4+k);for(unsigned xy=0;xy<59*24;++xy)for(unsigned k=1;k<4;++k)add(off+xy*4+k,off+xy*4+k-1);}}}
 int correction(unsigned source,unsigned target,int x,int ry,int q)const{if(q<=6)return 0;const int knots[5]={6,12,20,32,42};auto p=&values[(((size_t(source)*160+target)*59+x+29)*24+(ry>0?12:0)+std::abs(ry)-24)*4];int hi=1;while(hi<4&&q>knots[hi])++hi;int a=hi==1?0:p[hi-2],b=p[hi-1];return int(std::nearbyint(double(a)+double(b-a)*(q-knots[hi-1])/(knots[hi]-knots[hi-1])));}
};
