// Standalone lossless second-difference and zero-run encoding of the safe PDB.
#include "architecture_data.hpp"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
int main(int argc,char** argv) {
 try {
    if(argc!=3)throw std::runtime_error("compress_phase_bounds dictionary.bin safe.bin");
    std::ifstream in(argv[1],std::ios::binary);std::ofstream out(argv[2],std::ios::binary);
    auto read=[&](void* p,size_t n){if(!in.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated input");};
    char magic[8];read(magic,8);if(std::string(magic,8)!="PHASELD2")throw std::runtime_error("Bad source magic");
    uint32_t header[7];read(header,sizeof(header));if(header[0]!=1 || header[1]!=496 || header[2]!=160 || header[3]!=4 || header[4]!=10 || header[5]!=10 || header[6]!=12)throw std::runtime_error("Bad source dimensions");
    std::array<uint16_t,160> ports;read(ports.data(),ports.size()*2);size_t count=4*496*160;
    uint32_t info[3];read(info,sizeof(info));in.seekg(count*(2+info[2])+uint64_t(info[1])*info[0]*12*2,std::ios::cur);
    read(info,sizeof(info));if(info[0]!=10 || info[1]>count || (info[2]!=2 && info[2]!=4))throw std::runtime_error("Bad dictionary");
    std::vector<char> metadata(count*(2+info[2]));read(metadata.data(),metadata.size());
    std::vector<uint16_t> values(info[1]*120);read(values.data(),values.size()*2);
    std::vector<unsigned char> stream;stream.reserve(values.size());
    auto varint=[&](uint32_t v){do {stream.push_back(static_cast<unsigned char>((v&127)|(v>=128?128:0)));v>>=7;}while(v);};
    uint32_t zeros=0;
    auto flush=[&]{if(zeros){varint(0);varint(zeros);zeros=0;}};
    for(size_t n=0;n<values.size();++n) {
        int x=int((n%120)/12),y=int(n%12),prediction=0;
        if(x)prediction+=values[n-12];if(y)prediction+=values[n-1];if(x && y)prediction-=values[n-13];
        int delta=int(values[n])-prediction;
        if(!delta){++zeros;continue;}flush();uint32_t zigzag=delta>=0?uint32_t(delta)*2:uint32_t(-delta)*2-1;varint(zigzag+1);
    }
    flush();
    size_t cursor=0;uint32_t run=0;std::vector<uint16_t> decoded(values.size());
    auto get=[&]{uint32_t v=0;unsigned shift=0;while(true){if(cursor>=stream.size() || shift>=35)throw std::runtime_error("Invalid compressed varint");unsigned b=stream[cursor++];v|=(b&127)<<shift;if(!(b&128))return v;shift+=7;}};
    for(size_t n=0;n<decoded.size();++n) {
        int delta=0;if(run)--run;else {auto code=get();if(!code){auto zeros=get();if(!zeros || zeros>decoded.size()-n)throw std::runtime_error("Invalid zero run");run=zeros-1;}else{--code;delta=(code&1)?-int((code+1)/2):int(code/2);}}
        int x=int((n%120)/12),y=int(n%12),prediction=0;if(x)prediction+=decoded[n-12];if(y)prediction+=decoded[n-1];if(x && y)prediction-=decoded[n-13];
        int value=prediction+delta;if(value<0 || value>65535 || value!=values[n])throw std::runtime_error("Phase roundtrip mismatch");decoded[n]=uint16_t(value);
    }
    if(cursor!=stream.size() || run)throw std::runtime_error("Phase stream not consumed");
    out.write("PHASELB4",8);out.write(archdata::HASH,64);uint32_t shape[]={1,496,160,4,10,12};out.write(reinterpret_cast<char*>(shape),sizeof(shape));out.write(reinterpret_cast<char*>(ports.data()),ports.size()*2);out.write(reinterpret_cast<char*>(info),sizeof(info));out.write(metadata.data(),metadata.size());uint64_t bytes=stream.size();out.write(reinterpret_cast<char*>(&bytes),8);out.write(reinterpret_cast<char*>(stream.data()),stream.size());
    if(!out)throw std::runtime_error("Output failure");std::cout<<"exact_roundtrip=1 decoded_values="<<values.size()<<" encoded_bytes="<<stream.size()<<" total_bytes="<<uint64_t(out.tellp())<<'\n';
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
