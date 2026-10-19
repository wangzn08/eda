#pragma once
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
class BufferedCsvWriter {
 FILE*file=nullptr;std::vector<char>buffer;size_t used=0;
 void flush(){if(used && std::fwrite(buffer.data(),1,used,file)!=used)throw std::runtime_error("CSV write failure");used=0;}
 void append(std::string_view text){if(text.size()>buffer.size())throw std::runtime_error("Oversized CSV field");if(used+text.size()>buffer.size())flush();std::memcpy(buffer.data()+used,text.data(),text.size());used+=text.size();}
public:
 explicit BufferedCsvWriter(const std::string&path):buffer(1<<20){file=std::fopen(path.c_str(),"wb");if(!file)throw std::runtime_error("CSV output open failure");std::setvbuf(file,nullptr,_IONBF,0);append("From,To,delay\n");}
 BufferedCsvWriter(const BufferedCsvWriter&)=delete;
 ~BufferedCsvWriter(){if(file)std::fclose(file);}
 void row(std::string_view source,std::string_view target,uint64_t delay){char digits[32];auto end=std::to_chars(digits,digits+32,delay);if(end.ec!=std::errc())throw std::runtime_error("Delay formatting failure");size_t n=source.size()+target.size()+size_t(end.ptr-digits)+3;if(n>buffer.size())throw std::runtime_error("Oversized CSV row");if(used+n>buffer.size())flush();char*dest=buffer.data()+used;std::memcpy(dest,source.data(),source.size());dest+=source.size();*dest++=',';std::memcpy(dest,target.data(),target.size());dest+=target.size();*dest++=',';std::memcpy(dest,digits,end.ptr-digits);dest+=end.ptr-digits;*dest='\n';used+=n;}
 // The caller supplies the already validated two-field span. This preserves
 // the original comma and removes a separate tiny copy for each endpoint.
 void row_pair(std::string_view pair,uint64_t delay){char digits[32];auto end=std::to_chars(digits,digits+32,delay);if(end.ec!=std::errc())throw std::runtime_error("Delay formatting failure");size_t n=pair.size()+size_t(end.ptr-digits)+2;if(n>buffer.size())throw std::runtime_error("Oversized CSV row");if(used+n>buffer.size())flush();char*dest=buffer.data()+used;std::memcpy(dest,pair.data(),pair.size());dest+=pair.size();*dest++=',';std::memcpy(dest,digits,end.ptr-digits);dest+=end.ptr-digits;*dest='\n';used+=n;}
 void finish(){flush();int result=std::fclose(file);file=nullptr;if(result)throw std::runtime_error("CSV close failure");}
};
