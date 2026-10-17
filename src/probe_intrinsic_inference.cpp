// Model-only screening on precomputed features; excludes estimator and CSV time.
#include <fstream>
#include <vector>
#include <iostream>
#include <ctime>
#include <cstdint>
#include <cmath>
struct N {uint16_t f,l=0,r=0;double v;};
int main(int argc,char**argv){try{if(argc!=4)throw std::runtime_error("model, feature file, prediction output required");std::ifstream m(argv[1],std::ios::binary);auto read=[&](void*p,size_t n){if(!m.read((char*)p,n))throw std::runtime_error("model truncated");};char magic[8];uint32_t nt;read(magic,8);read(&nt,4);if(std::string(magic,8)!="ASYBND01"||nt!=256)throw std::runtime_error("model mismatch");std::vector<std::vector<N>>trees;for(unsigned t=0;t<nt;++t){uint16_t n;read(&n,2);std::vector<N>a(n);for(auto&v:a){read(&v.f,2);if(v.f!=65535){read(&v.l,2);read(&v.r,2);}read(&v.v,8);}trees.push_back(std::move(a));}std::ifstream f(argv[2],std::ios::binary);uint32_t rows,cols;f.read((char*)&rows,4);f.read((char*)&cols,4);std::vector<float>x(size_t(rows)*cols);f.read((char*)x.data(),x.size()*4);if(!f||!rows||!cols)throw std::runtime_error("features truncated");std::ofstream out(argv[3],std::ios::binary);std::vector<double>p(rows);double checksum=0;auto start=std::clock();for(unsigned repeat=0;repeat<3;++repeat)for(unsigned i=0;i<rows;++i){auto*z=x.data()+size_t(i)*cols;double sum=0;for(auto&a:trees){unsigned j=0;while(a[j].f!=65535){auto&v=a[j];if(v.f>=cols)throw std::runtime_error("feature mismatch");j=double(z[v.f])<=v.v?v.l:v.r;}sum+=a[j].v;}p[i]=sum;checksum+=sum;}double cpu=double(std::clock()-start)/CLOCKS_PER_SEC;out.write((char*)p.data(),p.size()*8);std::cerr<<"rows="<<rows<<" columns="<<cols<<" repeats=3 cpu_seconds="<<cpu<<" checksum="<<checksum<<'\n';}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
