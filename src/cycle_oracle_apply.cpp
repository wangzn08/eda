#include "cycle_path_oracle.hpp"
#include <fstream>
#include <iostream>
#include <unordered_map>
#include <memory>

int main(int argc,char** argv) {
    try {
        if(argc!=4 && argc!=5) throw std::runtime_error("cycle_oracle_apply baseline.csv result.csv tail.bin [local.bin]");
        if(std::string(argv[1])==argv[2] || std::string(argv[3])==argv[2]) throw std::runtime_error("Distinct paths required");
        bool nominal=argc==5 && std::string(argv[4])=="--nominal";
        CyclePathOracle oracle(argv[3],nominal);
        std::unique_ptr<LocalPathOracle> local;
        if(argc==5 && !nominal) local=std::make_unique<LocalPathOracle>(argv[4]);
        std::unordered_map<std::string,uint32_t> sites,ports;
        for(size_t i=0;i<std::size(archdata::SITES);++i) {auto p=archdata::SITES[i];sites["SRB_"+std::to_string(p.x)+"_"+std::to_string(p.y)]=i;}
        for(int i=0;i<archdata::P;++i) ports[archdata::PORTS[i]]=i;
        auto pin=[&](const std::string& s){auto slash=s.find('/');return sites.at(s.substr(0,slash))*archdata::P+ports.at(s.substr(slash+1));};
        std::ifstream in(argv[1]);std::ofstream out(argv[2]);std::string line;
        if(!in || !out || !std::getline(in,line) || (line!="From,To,delay" && line!="From,To,delay\r")) throw std::runtime_error("Invalid baseline file");
        out<<"From,To,delay\n";uint64_t rows=0,changed=0;
        while(std::getline(in,line)) {
            auto comma=line.find(','),second=line.find(',',comma+1);
            if(comma==line.npos || second==line.npos) throw std::runtime_error("Invalid row");
            auto from=line.substr(0,comma),to=line.substr(comma+1,second-comma-1);
            uint64_t prior=std::stoull(line.substr(second+1)),value=local?std::min(prior,local->upper_bound(pin(from),pin(to))):prior;
            value=oracle.cap(pin(from),pin(to),value);
            out<<from<<','<<to<<','<<value<<'\n';++rows;changed+=value!=prior;
        }
        std::cerr<<"rows="<<rows<<" changed="<<changed<<'\n';
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
