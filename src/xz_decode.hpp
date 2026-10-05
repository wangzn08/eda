#pragma once
#include <cstddef>
extern "C" {
#include "vendor/xz/xz.h"
}
inline bool decode_xz_exact(const unsigned char*input,size_t input_size,unsigned char*output,size_t output_size){
 static const bool initialized=[](){xz_crc32_init();return true;}();(void)initialized;
 auto decoder=xz_dec_init(XZ_SINGLE,0);if(!decoder)return false;xz_buf buffer{};buffer.in=input;buffer.in_size=input_size;buffer.out=output;buffer.out_size=output_size;
 auto result=xz_dec_run(decoder,&buffer);xz_dec_end(decoder);return result==XZ_STREAM_END && buffer.in_pos==input_size && buffer.out_pos==output_size;
}
