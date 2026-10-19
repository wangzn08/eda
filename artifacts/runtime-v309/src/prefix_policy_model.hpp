#pragma once
#include "routing_search.hpp"
#include "xz_decode.hpp"
#include <fstream>
#include <cstring>
#include <array>

class PrefixPolicyModel {
 struct Tree{uint32_t offset,count;};
 struct PolicyNode{int32_t left,right;int16_t threshold;uint8_t feature,confidence;uint16_t first,second;};
 static_assert(sizeof(PolicyNode)==16);
 std::array<Tree,160>trees;
 std::vector<PolicyNode>nodes;
public:
 struct Actions{uint16_t first=65535,second=65535;unsigned confidence=0;};
 explicit PrefixPolicyModel(const std::string&path){
  std::ifstream f(path,std::ios::binary);char header[84]{};f.read(header,84);
  uint32_t features,count,bytes;std::memcpy(&features,header+72,4);std::memcpy(&count,header+76,4);std::memcpy(&bytes,header+80,4);
  if(!f||std::memcmp(header,"PPOLICY1",8)||std::memcmp(header+8,archdata::HASH,64)||features!=38||count!=160||bytes<1280||(bytes-1280)%16||bytes>30000000)throw std::runtime_error("Prefix policy header");
  std::vector<unsigned char>stream((std::istreambuf_iterator<char>(f)),{}),decoded(bytes);
  if(!decode_xz_exact(stream.data(),stream.size(),decoded.data(),decoded.size()))throw std::runtime_error("Prefix policy XZ");
  std::memcpy(trees.data(),decoded.data(),1280);nodes.resize((bytes-1280)/16);std::memcpy(nodes.data(),decoded.data()+1280,bytes-1280);
  for(auto t:trees){if(size_t(t.offset)+t.count>nodes.size())throw std::runtime_error("Policy tree range");for(unsigned i=0;i<t.count;++i){auto n=nodes[t.offset+i];if(n.feature==255){if(n.first>=496||n.second>=496)throw std::runtime_error("Policy action");}else if(n.feature>=38||n.left<=int(i)||n.right<=int(i)||unsigned(n.left)>=t.count||unsigned(n.right)>=t.count)throw std::runtime_error("Policy child/feature");}}
 }
 Actions select(unsigned core,unsigned target,int sx,int sy,int tx,int ty)const{
  if(core>=160||target>=496)throw std::runtime_error("Policy input");auto tree=trees[core];if(!tree.count)return {};
  int dx=tx-sx,dy=ty-sy,ax=std::abs(dx),ay=std::abs(dy),qx=ax>29?(ax-20)/10:0,qy=ay>35?(ay-24)/12:0;
  auto positive_mod=[](int v,int n){int r=v%n;return r<0?r+n:r;};int rx=(dx<0?-1:dx>0?1:0)*(ax-qx*10),ry=(dy<0?-1:dy>0?1:0)*(ay-qy*12);
  auto net=archdata::NETS[core];auto vector=archdata::VECTORS[net.vector];
  std::array<int,38>v={sx,sy,tx,ty,int(core),int(target),dx,dy,ax,ay,qx,qy,rx,ry,positive_mod(dx,10),positive_mod(dy,12),sy%100,ty%100,sx<16,tx<16,sy<100,ty<100,std::min(sx,tx)<76&&std::max(sx,tx)>89,std::min(sx,119-sx),std::min(tx,119-tx),std::min(sy,549-sy),std::min(ty,549-ty),std::min(sy%100,99-sy%100),std::min(ty%100,99-ty%100),sx>=76&&sx<=89,tx>=76&&tx<=89,int(core)/20,int(core)%20,int(target)/8,int(target)%8,vector.x,vector.y,int(net.delay)};
  unsigned i=0;for(unsigned depth=0;depth<=25;++depth){auto n=nodes[tree.offset+i];if(n.feature==255)return {n.first,n.second,n.confidence};i=unsigned(v[n.feature]<=n.threshold?n.left:n.right);}throw std::runtime_error("Policy depth");
 }
};
