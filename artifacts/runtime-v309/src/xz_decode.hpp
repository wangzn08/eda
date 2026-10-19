#pragma once
#include <cstddef>
#ifndef CORE_LIBLZMA
#define CORE_LIBLZMA 0
#endif
#if CORE_LIBLZMA
#include <lzma.h>
#else
extern "C" {
#include "vendor/xz/xz.h"
}
#endif
inline bool decode_xz_exact(const unsigned char*input,size_t input_size,unsigned char*output,size_t output_size){
 #if CORE_LIBLZMA
 uint64_t memory_limit=200000000;size_t in=0,out=0;auto result=lzma_stream_buffer_decode(&memory_limit,0,nullptr,input,&in,input_size,output,&out,output_size);return result==LZMA_OK && in==input_size && out==output_size;
 #else
 static const bool initialized=[](){xz_crc32_init();return true;}();(void)initialized;
 auto decoder=xz_dec_init(XZ_SINGLE,0);if(!decoder)return false;xz_buf buffer{};buffer.in=input;buffer.in_size=input_size;buffer.out=output;buffer.out_size=output_size;
 auto result=xz_dec_run(decoder,&buffer);xz_dec_end(decoder);return result==XZ_STREAM_END && buffer.in_pos==input_size && buffer.out_pos==output_size;
 #endif
}
