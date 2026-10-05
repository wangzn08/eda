#include "phase_lower_bound.hpp"
#include <iostream>
int main(int argc,char**argv){if(argc!=3)return 2;PhaseLowerBound a(argv[1]),b(argv[2]);uint64_t checked=0,mismatch=0;unsigned ports=0;for(int p=0;p<archdata::P;++p)if(b.compact_input(p)){++ports;for(int t=0;t<archdata::P;++t)for(int x=0;x<10;++x)for(int y=0;y<12;++y)for(int sx:{-1,1})for(int sy:{-1,1}){archdata::XY u{60,250},v{60+sx*(20+x),250+sy*(48+y)};mismatch+=a.lower(u,p,v,t)!=b.lower(u,p,v,t);++checked;}}std::cout<<"{\"ports\":"<<ports<<",\"queries_checked\":"<<checked<<",\"mismatches\":"<<mismatch<<"}\n";return mismatch?1:0;}
