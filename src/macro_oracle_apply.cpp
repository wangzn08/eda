#include "macro_path_oracle.hpp"
#include <fstream>
#include <iostream>
#include <unordered_map>
#include <ctime>
int main(int argc,char** argv) {
    try {
        if(argc!=5 && argc!=6)throw std::runtime_error("macro_oracle_apply bounds.csv result.csv tail.bin budget [--gap-heuristic]");
        if(std::string(argv[1])==argv[2] || std::string(argv[3])==argv[2])throw std::runtime_error("Distinct paths required");
        MacroPathOracle oracle(argv[3],argc==6 && std::string(argv[5])=="--gap-heuristic");unsigned budget=std::stoul(argv[4]);
        std::unordered_map<std::string,uint32_t> sites,ports;
        for(size_t i=0;i<std::size(archdata::SITES);++i) {auto p=archdata::SITES[i];sites["SRB_"+std::to_string(p.x)+"_"+std::to_string(p.y)]=i;}
        for(int i=0;i<archdata::P;++i)ports[archdata::PORTS[i]]=i;
        auto pin=[&](const std::string& s){auto k=s.find('/');return sites.at(s.substr(0,k))*archdata::P+ports.at(s.substr(k+1));};
        std::ifstream in(argv[1]);std::ofstream out(argv[2]);std::string line;
        if(!in || !out || !std::getline(in,line))throw std::runtime_error("Cannot open CSV");
        out<<"From,To,delay\n";uint64_t rows=0,changed=0;auto begin=std::clock();
        while(std::getline(in,line)) {
            auto c=line.find(','),d=line.find(',',c+1);if(c==line.npos || d==line.npos)throw std::runtime_error("Invalid row");
            auto s=line.substr(0,c),t=line.substr(c+1,d-c-1);uint64_t u=std::stoull(line.substr(d+1));auto v=oracle.cap(pin(s),pin(t),u,budget);
            out<<s<<','<<t<<','<<v<<'\n';++rows;changed+=v<u;
            if(rows%10000==0)std::cerr<<"progress="<<rows<<" changed="<<changed<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
        }
        std::cerr<<"rows="<<rows<<" changed="<<changed<<" expanded="<<oracle.total_expanded<<" finished="<<oracle.total_finished<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
