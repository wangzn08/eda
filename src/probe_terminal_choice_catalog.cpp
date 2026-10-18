#include "runtime_short_kernel.hpp"
#include "compact_response_kernel.hpp"
#include "initial_kernel_candidates.hpp"
#include "terminal_choice_catalog.hpp"
#include <fcntl.h>
#include <sys/stat.h>
class FrozenShortKernel{
 int fd=-1;unsigned char*mapping=nullptr;size_t bytes=0;const unsigned char*storage=nullptr;int minimum=0;
public:
 explicit FrozenShortKernel(const char*path){fd=open(path,O_RDONLY);struct stat st;if(fd<0||fstat(fd,&st))throw std::runtime_error("Frozen short file");bytes=st.st_size;mapping=(unsigned char*)mmap(nullptr,bytes,PROT_READ,MAP_PRIVATE,fd,0);if(mapping==MAP_FAILED)throw std::runtime_error("Frozen short mmap");if(std::memcmp(mapping,"RTSHORT1",8)||std::memcmp(mapping+8,archdata::HASH,64))throw std::runtime_error("Frozen short header");uint32_t h[6];std::memcpy(h,mapping+72,24);if(h[0]!=160||h[1]!=160||h[2]!=139||h[3]!=191||h[4]!=11)throw std::runtime_error("Frozen short shape");minimum=int32_t(h[5]);storage=mapping+96+139*2;}
 ~FrozenShortKernel(){if(mapping&&mapping!=MAP_FAILED)munmap(mapping,bytes);if(fd>=0)close(fd);}
 struct View{const unsigned char*lo=nullptr,*hi=nullptr;int minimum=0,slope=0,wl=0,wh=0,denominator=1;int get(unsigned t)const{int a=RuntimeShortKernel::View::raw(lo,t)+minimum;if(!hi)return a+slope;int b=RuntimeShortKernel::View::raw(hi,t)+minimum;return int(std::nearbyint(double(a*wl+b*wh)/denominator))+slope;}};
 View view(unsigned source,int dx,int dy)const{View v;v.minimum=minimum;int ax=std::abs(dx),qx=ax>29?(ax-20)/10:0;v.slope=qx*125+std::abs(dy)/12*(dy>0?127:125);auto row=[&](unsigned x,bool hi){auto p=storage+((size_t(x)*191+dy+95)*160+source)*220;if(hi)v.hi=p;else v.lo=p;};if(!qx){row(dx+29,false);return v;}constexpr int a[4]={1,3,6,9};unsigned lo=0,hi=3;for(unsigned k=0;k<4;++k){if(a[k]<=qx)lo=k;if(a[k]>=qx){hi=k;break;}}if(qx>=9)lo=hi=3;unsigned offset=59+(dx>0?40:0)+ax%10;row(offset+lo*10,false);if(lo!=hi){row(offset+hi*10,true);v.wl=a[hi]-qx;v.wh=qx-a[lo];v.denominator=a[hi]-a[lo];}return v;}
};
int main(int argc,char**argv){try{if(argc!=6)throw std::runtime_error("short packed, asset folder, geometry count required");auto start=std::clock();Graph g;std::string dir=argv[2];FrozenShortKernel sh(argv[1]);CompactResponseKernel near(dir+"/near-curves.bin"),far(dir+"/far-curves.bin");InitialKernelCandidates initial(g,dir+"/source-hints.bin");TerminalChoiceCatalog catalog(sh,near,far,initial.terminals,std::stoul(argv[3]),std::stoul(argv[4]),std::stoul(argv[5]));std::cout<<"cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
