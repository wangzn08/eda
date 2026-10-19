#pragma once
#include "xz_decode.hpp"
#include <cstdint>
#include <cstring>
#include <vector>
#include <stdexcept>
// Exact two-band response reconstruction. This changes storage, not distances.
inline void decode_transient_dictionary(const std::vector<unsigned char>&input,int16_t*dest,size_t bytes,unsigned period){
 if(input.size()<9||bytes%4||period==0)throw std::runtime_error("Transient dictionary metadata");uint32_t n,width;std::memcpy(&n,input.data(),4);std::memcpy(&width,input.data()+4,4);if(!n||n>1000000||(width!=2&&width!=4)||(width==2&&n>65536))throw std::runtime_error("Transient dictionary shape");size_t records=bytes/4;if(records%period)throw std::runtime_error("Transient dictionary period");std::vector<unsigned char>decoded(size_t(n)*4+records*width);if(!decode_xz_exact(input.data()+8,input.size()-8,decoded.data(),decoded.size()))throw std::runtime_error("Transient dictionary XZ");const auto*codes=decoded.data()+size_t(n)*4;for(size_t i=0;i<records;++i){uint32_t id=0;std::memcpy(&id,codes+i*width,width);if(id>=n)throw std::runtime_error("Transient dictionary index");size_t row=i/period,r=i%period;std::memcpy(&dest[row*period*2+r],decoded.data()+id*4,2);std::memcpy(&dest[row*period*2+period+r],decoded.data()+id*4+2,2);}
}
