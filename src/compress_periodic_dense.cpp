#include "architecture_data.hpp"
#include <array>
#include <fstream>
#include <vector>
#include <iostream>
#include <stdexcept>
#include <cstdint>
// Exact 2D residual encoding; raw inputs are architecture-derived path tables.
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("compress_periodic_dense base.raw conditioned.raw|- output.bin");
 std::ofstream out(argv[3],std::ios::binary);out.write("DENSECP1",8);out.write(archdata::HASH,64);
 uint32_t groups=std::string(argv[2])=="-"?1:2;out.write(reinterpret_cast<char*>(&groups),4);
 for(unsigned group=0;group<groups;++group){std::ifstream in(argv[1+group],std::ios::binary);char magic[8],hash[64];std::array<uint16_t,160>ports;in.read(magic,8);in.read(hash,64);in.read(reinterpret_cast<char*>(ports.data()),320);if(std::string(magic,8)!=(group?"ANCHOR03":"ANCHOR02") || std::string(hash,64)!=archdata::HASH)throw std::runtime_error("Bad raw asset");if(!group)out.write(reinterpret_cast<char*>(ports.data()),320);
  std::vector<std::pair<int,int>>shapes=group?std::vector<std::pair<int,int>>{{20,71},{24,59},{10,12},{10,12},{10,12},{10,12}}:std::vector<std::pair<int,int>>{{59,71}};
  uint64_t codes=0,zero_count=0,decoded_count=0;auto varint=[&](uint32_t value){do{out.put(char((value&127)|(value>=128?128:0)));value>>=7;++codes;}while(value);};auto flush=[&]{if(zero_count){varint(0);varint(uint32_t(zero_count));zero_count=0;}};
  for(int pair=0;pair<160*496;++pair)for(auto shape:shapes){int nx=shape.first,ny=shape.second;std::vector<uint16_t>v(nx*ny),check(v.size());in.read(reinterpret_cast<char*>(v.data()),v.size()*2);if(!in)throw std::runtime_error("Truncated raw table");for(int n=0;n<nx*ny;++n){int x=n/ny,y=n%ny,p=0;if(x)p+=v[n-ny];if(y)p+=v[n-1];if(x && y)p-=v[n-ny-1];int delta=int(v[n])-p;check[n]=uint16_t(p+delta);if(check[n]!=v[n])throw std::runtime_error("Roundtrip mismatch");if(!delta)++zero_count;else{flush();uint32_t z=delta>=0?uint32_t(delta)*2:uint32_t(-delta)*2-1;varint(z+1);}++decoded_count;}}
  flush();std::cerr<<"group="<<group<<" values="<<decoded_count<<" encoded_bytes="<<codes<<'\n';
 }
 if(!out)throw std::runtime_error("Compression output failure");std::cerr<<"total_bytes="<<out.tellp()<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
