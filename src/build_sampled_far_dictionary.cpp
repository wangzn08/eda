// Far response differences relative to exact nearby architecture curves.
// Validates all shared near points against the earlier near raw generation.
#include "architecture_data.hpp"
#include <array>
#include <algorithm>
#include <cstdint>
#include <ctime>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>
struct FarPattern{std::array<int16_t,38>v;};
static uint64_t pattern_hash(const FarPattern&p){uint64_t h=1469598103934665603ULL;const auto*b=reinterpret_cast<const unsigned char*>(p.v.data());for(unsigned i=0;i<72;i+=8){uint64_t v;std::memcpy(&v,b+i,8);h=(h^v)*1099511628211ULL;}uint32_t v;std::memcpy(&v,b+72,4);return (h^v)*1099511628211ULL;}
int main(int argc,char**argv){try{
 if(argc!=5&&argc!=6)throw std::runtime_error("Full raw, dictionary output, anchor digits, near raw, optional absolute required");bool absolute=argc==6&&std::string(argv[5])=="absolute";if(argc==6&&!absolute)throw std::runtime_error("Mode");
 std::vector<int16_t>xs;std::vector<uint32_t>anchors;for(char c:std::string(argv[3])){if(c<'1'||c>'9')throw std::runtime_error("Anchor");anchors.push_back(c-'0');}if(anchors.empty()||!std::is_sorted(anchors.begin(),anchors.end()))throw std::runtime_error("Anchors");for(int sign:{-1,1})for(auto a:anchors)for(int r=0;r<10;++r)xs.push_back(sign*(20+a*10+r));
 std::ifstream in(argv[1],std::ios::binary);char magic[8],hash[64];std::array<uint16_t,160>ports;std::array<uint32_t,6>shape;in.read(magic,8);in.read(hash,64);in.read(reinterpret_cast<char*>(ports.data()),320);in.read(reinterpret_cast<char*>(shape.data()),24);if(!in||std::string(magic,8)!="FDCRAW01"||std::string(hash,64)!=archdata::HASH||shape!=std::array<uint32_t,6>{160,160,239,24,46,2})throw std::runtime_error("Full header");
 std::ifstream near(argv[4],std::ios::binary);std::array<char,1056>nh;near.read(nh.data(),nh.size());uint32_t nearShape[6]={160,160,59,24,40,2};if(!near||std::memcmp(nh.data(),"CURVRAW2",8)||std::memcmp(nh.data()+8,hash,64)||std::memcmp(nh.data()+392,nearShape,24))throw std::runtime_error("Near header");
 size_t rows=size_t(160)*xs.size()*24,count=rows*160;std::vector<int16_t>offsets(count),slab(size_t(160)*239*24*46),nearSlab(size_t(160)*59*24*40);std::vector<uint32_t>codes(count),next;std::vector<FarPattern>patterns;std::unordered_map<uint64_t,uint32_t>heads;heads.reserve(300000);auto begin=std::clock();uint64_t shared=0;
 for(unsigned s=0;s<160;++s){in.read(reinterpret_cast<char*>(slab.data()),slab.size()*2);near.read(reinterpret_cast<char*>(nearSlab.data()),nearSlab.size()*2);if(!in||!near)throw std::runtime_error("Raw slab");
  for(unsigned t=0;t<160;++t)for(int x=-29;x<=29;++x)for(unsigned y=0;y<24;++y)for(unsigned q=8;q<46;++q){auto a=slab[((size_t(t)*239+x+119)*24+y)*46+q],b=nearSlab[((size_t(t)*59+x+29)*24+y)*40+q-8];if(a!=b)throw std::runtime_error("Shared near cost mismatch");++shared;}
  for(unsigned t=0;t<160;++t)for(unsigned xi=0;xi<xs.size();++xi)for(unsigned y=0;y<24;++y){int x=xs[xi],reference=(x<0?-1:1)*(20+std::abs(x)%10);size_t a=((size_t(t)*239+x+119)*24+y)*46,b=((size_t(t)*239+reference+119)*24+y)*46;int base=int(slab[a+8])-(absolute?0:slab[b+8]);if(base<INT16_MIN||base>INT16_MAX)throw std::runtime_error("Offset range");FarPattern p{};for(unsigned q=0;q<38;++q){int value=int(slab[a+q+8])-(absolute?0:slab[b+q+8])-base;if(value<INT16_MIN||value>INT16_MAX)throw std::runtime_error("Pattern range");p.v[q]=value;}
   uint64_t h=pattern_hash(p);auto found=heads.find(h);uint32_t id=UINT32_MAX;if(found!=heads.end())for(auto i=found->second;i!=UINT32_MAX;i=next[i])if(patterns[i].v==p.v){id=i;break;}if(id==UINT32_MAX){if(patterns.size()>=3000000)throw std::runtime_error("Pattern budget exceeded");id=patterns.size();patterns.push_back(p);next.push_back(found==heads.end()?UINT32_MAX:found->second);heads[h]=id;}size_t row=((size_t(t)*xs.size()+xi)*24+y)*160+s;offsets[row]=base;codes[row]=id;
  }
  if(s%8==7)std::cerr<<"source="<<s<<" patterns="<<patterns.size()<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }
 std::ofstream out(argv[2],std::ios::binary);out.write(absolute?"FDXDICT2":"FDXDICT1",8);out.write(hash,64);out.write(reinterpret_cast<char*>(ports.data()),320);uint32_t dims[8]={160,160,uint32_t(xs.size()),24,8,38,uint32_t(patterns.size()),4};out.write(reinterpret_cast<char*>(dims),32);uint32_t anchorCount=anchors.size();out.write(reinterpret_cast<char*>(&anchorCount),4);out.write(reinterpret_cast<char*>(anchors.data()),anchors.size()*4);out.write(reinterpret_cast<char*>(xs.data()),xs.size()*2);out.write(reinterpret_cast<char*>(offsets.data()),offsets.size()*2);out.write(reinterpret_cast<char*>(patterns.data()),patterns.size()*76);out.write(reinterpret_cast<char*>(codes.data()),codes.size()*4);if(!out)throw std::runtime_error("Dictionary output");std::cerr<<"bytes="<<uint64_t(out.tellp())<<" patterns="<<patterns.size()<<" shared_near_exact_points="<<shared<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
