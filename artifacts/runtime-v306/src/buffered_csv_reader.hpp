#pragma once
#include <cstdio>
#include <functional>
#include <cstring>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
class BufferedCsvReader {
 FILE* file=nullptr;std::vector<char> buffer;size_t begin=0,end=0;bool eof=false;std::function<void()>before_refill;
public:
 explicit BufferedCsvReader(const std::string&path):buffer(1<<20){file=std::fopen(path.c_str(),"rb");if(!file)throw std::runtime_error("CSV input open failure");std::setvbuf(file,nullptr,_IONBF,0);}
 ~BufferedCsvReader(){if(file)std::fclose(file);}
 void set_before_refill(std::function<void()>callback){before_refill=std::move(callback);}
 bool next(std::string_view&line){for(;;){const char*start=buffer.data()+begin;const void*stop=std::memchr(start,'\n',end-begin);if(stop){size_t length=static_cast<const char*>(stop)-start;line={start,length};begin+=length+1;return true;}if(eof){if(begin==end)return false;line={start,end-begin};begin=end;return true;}if(before_refill)before_refill();size_t left=end-begin;if(left==buffer.size())throw std::runtime_error("Oversized CSV line");if(left)std::memmove(buffer.data(),start,left);begin=0;size_t n=std::fread(buffer.data()+left,1,buffer.size()-left,file);end=left+n;if(n==0){if(std::ferror(file))throw std::runtime_error("CSV input read failure");eof=true;}}}
};
