// Lossless normalized curve dictionary, built without request/golden labels.
// Input rows are source-major; output lookup arrays have adjacent source cores.
#include "routing_search.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <unordered_map>
#include <ctime>
#include <cstring>
struct FullCurveKey {std::array<int16_t,46>values;};
uint64_t curve_hash(const FullCurveKey&k){uint64_t h=1469598103934665603ULL;const auto*p=reinterpret_cast<const unsigned char*>(k.values.data());for(unsigned i=0;i<88;i+=8){uint64_t v;std::memcpy(&v,p+i,8);h=(h^v)*1099511628211ULL;}uint32_t v;std::memcpy(&v,p+88,4);return (h^v)*1099511628211ULL;}
int main(int argc,char**argv){try{
 if(argc!=6)throw std::runtime_error("Raw input, dictionary output, source count, first period, period count required");unsigned sources=std::stoul(argv[3]),first=std::stoul(argv[4]),periods=std::stoul(argv[5]);if(!sources||sources>160||!periods||first+periods>46)throw std::runtime_error("Source or period range");
 std::ifstream in(argv[1],std::ios::binary);char magic[8],hash[64];std::array<uint16_t,160>ports;std::array<uint32_t,6>shape;in.read(magic,8);in.read(hash,64);in.read(reinterpret_cast<char*>(ports.data()),320);in.read(reinterpret_cast<char*>(shape.data()),24);if(!in||std::string(magic,8)!="FDCRAW01"||std::string(hash,64)!=archdata::HASH||shape!=std::array<uint32_t,6>{160,160,239,24,46,2})throw std::runtime_error("Raw header");
 constexpr size_t per_source=size_t(160)*239*24;size_t count=per_source*sources;if(std::filesystem::file_size(argv[1])<416+count*46*2)throw std::runtime_error("Incomplete raw source range");
 std::vector<int16_t>offsets(count);std::vector<uint32_t>codes(count),next;std::vector<FullCurveKey>patterns;std::unordered_map<uint64_t,uint32_t>heads;heads.reserve(200000);std::vector<int16_t>slab(per_source*46);auto begin=std::clock();
 for(unsigned source=0;source<sources;++source){in.read(reinterpret_cast<char*>(slab.data()),slab.size()*2);if(!in)throw std::runtime_error("Raw source read");for(size_t row=0;row<per_source;++row){int base=slab[row*46+8];FullCurveKey key{};for(unsigned q=0;q<periods;++q){int v=int(slab[row*46+first+q])-base;if(v<-32768||v>32767)throw std::runtime_error("Normalized curve overflow");key.values[q]=int16_t(v);}uint64_t h=curve_hash(key);auto found=heads.find(h);uint32_t code=UINT32_MAX;if(found!=heads.end())for(uint32_t p=found->second;p!=UINT32_MAX;p=next[p])if(patterns[p].values==key.values){code=p;break;}if(code==UINT32_MAX){if(patterns.size()>=3000000)throw std::runtime_error("Pattern working budget exceeded");code=patterns.size();next.push_back(found==heads.end()?UINT32_MAX:found->second);patterns.push_back(key);heads[h]=code;}size_t pos=row*sources+source;offsets[pos]=int16_t(base);codes[pos]=code;}
 std::cerr<<"source="<<source<<" patterns="<<patterns.size()<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';}
 std::ofstream out(argv[2],std::ios::binary);out.write("FDCDICT2",8);out.write(hash,64);out.write(reinterpret_cast<char*>(ports.data()),320);uint32_t description[8]={sources,160,239,24,first,periods,uint32_t(patterns.size()),4};out.write(reinterpret_cast<char*>(description),32);out.write(reinterpret_cast<char*>(offsets.data()),offsets.size()*2);for(const auto&p:patterns)out.write(reinterpret_cast<const char*>(p.values.data()),periods*2);out.write(reinterpret_cast<char*>(codes.data()),codes.size()*4);if(!out)throw std::runtime_error("Dictionary write");std::cerr<<"bytes="<<uint64_t(out.tellp())<<" patterns="<<patterns.size()<<" rows="<<count<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
