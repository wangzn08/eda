#pragma once
#include "runtime_memory.hpp"
#include <memory>
#include <utility>
// Flat exact mask->palette-ID map. Mmap growth immediately releases old pages
// instead of retaining millions of individually allocated hash nodes.
class MaskPaletteIndex{
 std::unique_ptr<MappedBytes>memory;size_t capacity=0,count=0;
 static size_t hash(uint32_t v){v^=v>>16;v*=0x7feb352du;v^=v>>15;v*=0x846ca68bu;v^=v>>16;return v;}
 void grow(){size_t next=capacity?capacity*2:16;auto m=std::make_unique<MappedBytes>(next*8);auto*dst=reinterpret_cast<uint64_t*>(m->data());if(memory){const auto*old=reinterpret_cast<const uint64_t*>(memory->data());for(size_t i=0;i<capacity;++i)if(old[i]){size_t j=hash(uint32_t(old[i]))&(next-1);while(dst[j])j=(j+1)&(next-1);dst[j]=old[i];}}memory=std::move(m);capacity=next;}
public:
 std::pair<unsigned,bool>intern(uint32_t mask,unsigned new_id){if(!mask)throw std::runtime_error("Zero palette mask");if(!capacity)grow();for(;;){auto*p=reinterpret_cast<uint64_t*>(memory->data());size_t i=hash(mask)&(capacity-1);while(p[i]&&uint32_t(p[i])!=mask)i=(i+1)&(capacity-1);if(p[i])return {unsigned(p[i]>>32),false};if((count+1)*4>capacity*3){grow();continue;}p[i]=(uint64_t(new_id)<<32)|mask;++count;return {new_id,true};}}
};
