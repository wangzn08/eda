#pragma once
#include "routing_search.hpp"
// Epoch-scoped dynamic programming workspace. No result survives a query epoch.
class PrefixDpWorkspace {
 struct Entry{uint64_t key=0;Distance value=0;uint32_t epoch=0;uint16_t action=65535;};
 std::vector<Entry>table;uint32_t epoch=0;
 static size_t hash(uint64_t key){key^=key>>16;key*=0x9e3779b97f4a7c15ULL;key^=key>>29;return size_t(key)&65535;}
public:
 void begin(){if(table.empty())table.resize(65536);if(++epoch==0){for(auto&e:table)e.epoch=0;epoch=1;}}
 bool get(uint64_t key,Distance&value)const{size_t slot=hash(key);for(unsigned j=0;j<16;++j){const auto&e=table[(slot+j)&65535];if(e.epoch!=epoch)return false;if(e.key==key){value=e.value;return true;}}return false;}
 uint16_t action(uint64_t key)const{size_t slot=hash(key);for(unsigned j=0;j<16;++j){const auto&e=table[(slot+j)&65535];if(e.epoch!=epoch)return 65535;if(e.key==key)return e.action;}return 65535;}
 void put(uint64_t key,Distance value,uint16_t action=65535){size_t slot=hash(key);for(unsigned j=0;j<16;++j){auto&e=table[(slot+j)&65535];if(e.epoch!=epoch||e.key==key){e={key,value,epoch,action};return;}}}
};
