#include "macro_path_oracle.hpp"
#include <fstream>
#include <iostream>
#include <unordered_map>
#include <ctime>
int main(int argc,char** argv) {
    try {
        if(argc<5)throw std::runtime_error("macro_oracle_apply bounds.csv result.csv tail.bin budget [--gap-heuristic] [--repeat-jumps] [--phase-bounds file]");
        if(std::string(argv[1])==argv[2] || std::string(argv[3])==argv[2])throw std::runtime_error("Distinct paths required");
        bool gaps=false,jumps=false,bridges=false,doubling=false,all_ports=false,short_jumps=false;double weight=1;std::unique_ptr<PhaseLowerBound>phase;
        for(int i=5;i<argc;++i){std::string arg=argv[i];if(arg=="--short-repeat-jumps")short_jumps=true;else if(arg=="--all-net-ports")all_ports=true;else if(arg=="--cycle-doubling")doubling=true;else if(arg=="--gap-heuristic")gaps=true;else if(arg=="--repeat-jumps")jumps=true;else if(arg=="--local-bridges")bridges=true;else if(arg=="--priority-weight" && i+1<argc)weight=std::stod(argv[++i]);else if(arg=="--phase-bounds" && i+1<argc){if(std::string(argv[i+1])==argv[2])throw std::runtime_error("Output differs from phase asset");phase=std::make_unique<PhaseLowerBound>(argv[++i]);}else throw std::runtime_error("Unknown macro option");}
        MacroPathOracle oracle(argv[3],gaps,jumps,phase.get(),bridges,weight,doubling,all_ports,short_jumps);unsigned budget=std::stoul(argv[4]);
        std::unordered_map<std::string,uint32_t> sites,ports;
        for(size_t i=0;i<std::size(archdata::SITES);++i) {auto p=archdata::SITES[i];sites["SRB_"+std::to_string(p.x)+"_"+std::to_string(p.y)]=i;}
        for(int i=0;i<archdata::P;++i)ports[archdata::PORTS[i]]=i;
        auto pin=[&](const std::string& s){auto k=s.find('/');return sites.at(s.substr(0,k))*archdata::P+ports.at(s.substr(k+1));};
        std::ifstream in(argv[1]);std::ofstream out(argv[2]);std::string line;
        if(!in || !out || !std::getline(in,line))throw std::runtime_error("Cannot open CSV");
        out<<"From,To,delay\n";uint64_t rows=0,changed=0;auto begin=std::clock();
        while(std::getline(in,line)) {
            auto c=line.find(','),d=line.find(',',c+1);if(c==line.npos || d==line.npos)throw std::runtime_error("Invalid row");
            auto s=line.substr(0,c),t=line.substr(c+1,d-c-1);uint64_t u=std::stoull(line.substr(d+1));if(u>=100000000)u=INF;auto v=oracle.cap(pin(s),pin(t),u,budget);
            out<<s<<','<<t<<','<<v<<'\n';++rows;changed+=v<u;
            if(rows%10000==0)std::cerr<<"progress="<<rows<<" changed="<<changed<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
        }
        std::cerr<<"rows="<<rows<<" changed="<<changed<<" expanded="<<oracle.total_expanded<<" finished="<<oracle.total_finished<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
