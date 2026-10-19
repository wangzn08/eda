#pragma once
#include <stdexcept>
#include <fstream>
#include <vector>
#include <iostream>
#include <sys/mman.h>
#include <unistd.h>
#include <sys/resource.h>
#if defined(__APPLE__)
#include <malloc/malloc.h>
#include <mach/mach.h>
#elif defined(__GLIBC__)
#include <malloc.h>
#endif
inline void release_unused_heap_pages(){
#if defined(__APPLE__)
 malloc_zone_pressure_relief(nullptr,0);
#elif defined(__GLIBC__)
 malloc_trim(0);
#endif
}
inline void runtime_memory_checkpoint(const char*label){
#if defined(__APPLE__)
 mach_task_basic_info_data_t info{};mach_msg_type_number_t n=MACH_TASK_BASIC_INFO_COUNT;struct rusage r{};getrusage(RUSAGE_SELF,&r);if(task_info(mach_task_self(),MACH_TASK_BASIC_INFO,reinterpret_cast<task_info_t>(&info),&n)==KERN_SUCCESS)std::cerr<<"memory_stage="<<label<<" resident_bytes="<<info.resident_size<<" peak_rss_bytes="<<r.ru_maxrss<<'\n';
#endif
}
class MappedBytes{
 unsigned char*p=nullptr;size_t bytes=0;
public:
 explicit MappedBytes(size_t n):bytes(n){p=static_cast<unsigned char*>(mmap(nullptr,n,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0));if(p==MAP_FAILED){p=nullptr;throw std::runtime_error("Decode allocation");}}
 ~MappedBytes(){if(p)munmap(p,bytes);}MappedBytes(const MappedBytes&)=delete;MappedBytes&operator=(const MappedBytes&)=delete;
 unsigned char*data(){return p;}const unsigned char*data()const{return p;}size_t size()const{return bytes;}
};
inline std::vector<unsigned char>read_remaining_asset(std::ifstream&f){auto start=f.tellg();f.seekg(0,std::ios::end);auto length=f.tellg()-start;if(!f||length<=0||length>100000000)throw std::runtime_error("Asset payload length");f.seekg(start);std::vector<unsigned char>v(static_cast<size_t>(length));f.read(reinterpret_cast<char*>(v.data()),length);if(!f)throw std::runtime_error("Asset payload read");return v;}
