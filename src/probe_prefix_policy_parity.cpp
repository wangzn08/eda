#include "prefix_policy_model.hpp"
#include <iostream>
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Policy model and parity sample required");
 PrefixPolicyModel model(argv[1]);std::ifstream f(argv[2],std::ios::binary);
 if(!f)throw std::runtime_error("Policy sample open");char bytes[18];unsigned count=0;
 while(f.read(bytes,18)){uint16_t v[8];std::memcpy(v,bytes,16);auto actions=model.select(v[4],v[5],v[0],v[1],v[2],v[3]);if(actions.first!=v[6]||actions.second!=v[7]||actions.confidence!=uint8_t(bytes[16]))throw std::runtime_error("Policy native feature/action parity");++count;}
 if(!f.eof()||f.gcount())throw std::runtime_error("Policy sample incomplete");
 std::cout<<"matched="<<count<<'\n';
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
