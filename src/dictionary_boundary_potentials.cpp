// Deduplicate complete 24-component physical penalty vectors without labels.
#include "architecture_data.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>
struct PhiPattern{std::array<int16_t,24>v;};
uint64_t phi_hash(const PhiPattern&p){uint64_t h=1469598103934665603ULL;const auto*b=reinterpret_cast<const unsigned char*>(p.v.data());for(unsigned i=0;i<48;i+=8){uint64_t v;std::memcpy(&v,b+i,8);h=(h^v)*1099511628211ULL;}return h;}
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Raw phi field and output required");std::ifstream f(argv[1],std::ios::binary);std::array<char,92>h;f.read(h.data(),h.size());uint32_t dims[5]={2,3,uint32_t(std::size(archdata::SITES)),160,4};if(!f||std::memcmp(h.data(),"PHIPEN01",8)||std::memcmp(h.data()+8,archdata::HASH,64)||std::memcmp(h.data()+72,dims,20))throw std::runtime_error("Phi raw header");
 size_t rows=std::size(archdata::SITES)*160;std::vector<int16_t>data(rows*24);f.read(reinterpret_cast<char*>(data.data()),data.size()*2);if(!f||f.peek()!=EOF)throw std::runtime_error("Phi raw body");std::vector<uint32_t>codes(rows),next;std::vector<PhiPattern>patterns;std::unordered_map<uint64_t,uint32_t>heads;heads.reserve(200000);
 for(size_t row=0;row<rows;++row){PhiPattern p;for(unsigned group=0;group<6;++group)for(unsigned d=0;d<4;++d)p.v[group*4+d]=data[(size_t(group)*rows+row)*4+d];auto hash=phi_hash(p);auto found=heads.find(hash);uint32_t id=UINT32_MAX;if(found!=heads.end())for(auto i=found->second;i!=UINT32_MAX;i=next[i])if(patterns[i].v==p.v){id=i;break;}if(id==UINT32_MAX){if(patterns.size()>=3000000)throw std::runtime_error("Phi pattern budget");id=patterns.size();patterns.push_back(p);next.push_back(found==heads.end()?UINT32_MAX:found->second);heads[hash]=id;}codes[row]=id;}
 for(size_t row=0;row<rows;++row)for(unsigned group=0;group<6;++group)for(unsigned d=0;d<4;++d)if(patterns[codes[row]].v[group*4+d]!=data[(size_t(group)*rows+row)*4+d])throw std::runtime_error("Phi complete parity");
 std::ofstream out(argv[2],std::ios::binary);out.write("PHDICT01",8);out.write(archdata::HASH,64);uint32_t shape[4]={uint32_t(std::size(archdata::SITES)),160,24,uint32_t(patterns.size())};out.write(reinterpret_cast<char*>(shape),16);out.write(reinterpret_cast<char*>(patterns.data()),patterns.size()*48);out.write(reinterpret_cast<char*>(codes.data()),codes.size()*4);if(!out)throw std::runtime_error("Phi output");std::cerr<<"rows="<<rows<<" patterns="<<patterns.size()<<" complete_vector_parity="<<rows<<" bytes="<<uint64_t(out.tellp())<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
