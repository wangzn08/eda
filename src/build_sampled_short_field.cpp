// Architecture-only scalar field. Rotate both port lanes in the indexing,
// then retain exact successive-lane cost differences; weights are not assumed
// lane invariant. Far samples store differences from a nearby reference.
#include "architecture_data.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <iostream>
#include <limits>
#include <vector>
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("raw curves and output required");
 std::ifstream raw(argv[1],std::ios::binary);char magic[8],hash[64];std::array<uint16_t,160>ports;std::array<uint32_t,6>shape;
 raw.read(magic,8);raw.read(hash,64);raw.read(reinterpret_cast<char*>(ports.data()),320);raw.read(reinterpret_cast<char*>(shape.data()),24);
 if(!raw||std::string(magic,8)!="FDCRAW01"||std::string(hash,64)!=archdata::HASH||shape!=std::array<uint32_t,6>{160,160,239,24,46,2})throw std::runtime_error("Curve header");
 std::vector<int16_t>xs;for(int x=-29;x<=29;++x)xs.push_back(x);for(int sign:{-1,1})for(int a:{1,4,8})for(int r=0;r<10;++r)xs.push_back(sign*(20+a*10+r));
 constexpr size_t count=size_t(160)*119*24*8*160;
 std::vector<int16_t>field(count),source(size_t(160)*239*24*46);int minimum=INT32_MAX,maximum=INT32_MIN;auto begin=std::clock();
 for(unsigned si=0;si<160;++si){raw.read(reinterpret_cast<char*>(source.data()),source.size()*2);if(!raw)throw std::runtime_error("Source read");unsigned lane=si/20,type=si%20,logicalSource=type*8+lane;
  for(unsigned logicalTarget=0;logicalTarget<160;++logicalTarget){unsigned ti=((logicalTarget%8+lane)%8)*20+logicalTarget/8;
   for(unsigned xi=0;xi<xs.size();++xi){int x=xs[xi],reference=(x<0?-1:1)*(20+std::abs(x)%10);
    for(unsigned y=0;y<24;++y)for(unsigned q=0;q<8;++q){size_t in=((size_t(ti)*239+x+119)*24+y)*46+q;int value=source[in];if(xi>=59)value-=source[((size_t(ti)*239+reference+119)*24+y)*46+q];
     if(value<INT16_MIN||value>INT16_MAX)throw std::runtime_error("Scalar range");minimum=std::min(minimum,value);maximum=std::max(maximum,value);size_t out=((((size_t(logicalTarget)*119+xi)*24+y)*8+q)*160+logicalSource);field[out]=value;
    }
   }
  }
  if(si%16==15)std::cerr<<"source="<<si<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }
 unsigned encodedMax=0;auto*encoded=reinterpret_cast<uint16_t*>(field.data());
 for(size_t i=0;i<count;i+=8){int previous=0;for(unsigned lane=0;lane<8;++lane){int current=field[i+lane],difference=current-previous;previous=current;if(difference<INT16_MIN||difference>INT16_MAX)throw std::runtime_error("Lane difference range");unsigned z=difference>=0?unsigned(difference)*2:unsigned(-difference)*2-1;encoded[i+lane]=z;encodedMax=std::max(encodedMax,z);}}
 std::ofstream out(argv[2],std::ios::binary);out.write("FDSHORT1",8);out.write(hash,64);out.write(reinterpret_cast<char*>(ports.data()),320);uint32_t description[8]={160,160,119,24,8,2,1,0};out.write(reinterpret_cast<char*>(description),32);out.write(reinterpret_cast<char*>(xs.data()),xs.size()*2);int32_t range[2]={minimum,maximum};out.write(reinterpret_cast<char*>(range),8);out.write(reinterpret_cast<char*>(field.data()),count*2);if(!out)throw std::runtime_error("Output");
 std::cerr<<"count="<<count<<" min="<<minimum<<" max="<<maximum<<" zigzag_max="<<encodedMax<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
