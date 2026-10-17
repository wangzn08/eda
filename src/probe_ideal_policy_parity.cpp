#include "ideal_action_policy.hpp"
#include <iostream>
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Ideal policy and sample required");IdealActionPolicy model(argv[1]);std::ifstream f(argv[2],std::ios::binary);char row[10];unsigned count=0;
 while(f.read(row,10)){uint16_t source,target;int16_t dx,dy;std::memcpy(&source,row,2);std::memcpy(&target,row+2,2);std::memcpy(&dx,row+4,2);std::memcpy(&dy,row+6,2);if(model.select(source,target,dx,dy)!=uint8_t(row[8]))throw std::runtime_error("Ideal action anchor mismatch");++count;}
 if(!f.eof()||f.gcount())throw std::runtime_error("Incomplete ideal sample");std::cout<<"matched="<<count<<'\n';
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
