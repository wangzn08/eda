// Standalone architecture-derived precision profile; no learned model required.
#include "routing_search.hpp"
#include "cycle_path_oracle.hpp"
#include <ctime>
#include <fstream>
#include <iostream>
#include <memory>
#include <filesystem>
std::string_view strip(std::string_view s) {
    auto a=s.find_first_not_of(" \r\n\t"),b=s.find_last_not_of(" \r\n\t");return a==s.npos?std::string_view{}:s.substr(a,b-a+1);
}
int main(int argc,char** argv) {
 try {
    auto directory=std::filesystem::absolute(argv[0]).parent_path();
    std::string input,output,phase=(directory/"phase-bounds.bin").string(),tail=(directory/"long-tail.bin").string(),certificate;
    double error=.00024,weight=1;bool use_cache=true,progress=false,dense=false,memo=false;
    for(int i=1;i<argc;++i) {
        std::string arg=argv[i];if(arg=="--help"){std::cout<<"phase_estimate -in requests.csv -out result.csv [--phase-bounds file] [--cycle-oracle file] [--relative-error number] [--weighted factor (research, no certificate)] [--no-cache] [--certificate file (no-cache)] [--progress]\n";return 0;}
        if(arg=="--memo-phase"){memo=true;continue;}if(arg=="--dense-phase"){dense=true;continue;}if(arg=="--no-cache"){use_cache=false;continue;}if(arg=="--progress"){progress=true;continue;}
        if(i+1==argc)throw std::runtime_error("Missing argument");
        if(arg=="-in")input=argv[++i];else if(arg=="-out")output=argv[++i];else if(arg=="--phase-bounds")phase=argv[++i];else if(arg=="--cycle-oracle")tail=argv[++i];else if(arg=="--weighted")weight=std::stod(argv[++i]);else if(arg=="--relative-error")error=std::stod(argv[++i]);else if(arg=="--certificate")certificate=argv[++i];else throw std::runtime_error("Unknown option");
    }
    if(memo && weight>1)throw std::runtime_error("Memo currently requires certified search");
    if(!std::isfinite(weight) || weight<1 || weight>4 || (weight>1 && !certificate.empty()))throw std::runtime_error("Weighted research mode cannot emit certificates");
    if(input.empty() || output.empty() || !std::isfinite(error) || error<0 || error>.1)throw std::runtime_error("Invalid input or relative error");
    auto normalized=[](const std::string& p){return std::filesystem::weakly_canonical(std::filesystem::absolute(p));};
    if(normalized(output)==normalized(input) || normalized(output)==normalized(phase) || normalized(output)==normalized(tail))throw std::runtime_error("Output must be distinct from inputs/assets");
    if(!certificate.empty() && (use_cache || normalized(certificate)==normalized(input) || normalized(certificate)==normalized(output) || normalized(certificate)==normalized(phase) || normalized(certificate)==normalized(tail)))throw std::runtime_error("Certificates require --no-cache and distinct files");
    auto begin=std::clock();PhaseLowerBound bounds(phase,dense);CyclePathOracle upper(tail);Graph graph;CompactSolver solver(graph);FastPinParser parser;
    double initialization=double(std::clock()-begin)/CLOCKS_PER_SEC;
    std::unique_ptr<PredictionCache> cache;if(use_cache)cache=std::make_unique<PredictionCache>();
    std::ifstream in(input);std::ofstream out(output),cert;std::vector<char> buffer(1<<20);out.rdbuf()->pubsetbuf(buffer.data(),buffer.size());
    if(!certificate.empty()){cert.open(certificate);cert<<"row,lower,upper,settled,relaxations\n";}
    std::string line;if(!in || !out || !std::getline(in,line) || strip(line)!="From,To")throw std::runtime_error("Input header must be From,To");
    out<<"From,To,delay\n";uint64_t rows=0;
    while(std::getline(in,line)) {
        auto text=strip(line);if(text.empty())continue;auto comma=text.find(',');if(comma==text.npos || text.find(',',comma+1)!=text.npos)throw std::runtime_error("Invalid request row");
        auto s=strip(text.substr(0,comma)),t=strip(text.substr(comma+1));Node from=parser.pin(s),to=parser.pin(t);Distance delay=INF;uint64_t key=(uint64_t(from)<<32)|to;SearchStats stats;
        if(!cache || !cache->get(key,delay)){Distance u=upper.cap(from,to,INF,true);delay=weight>1?solver.solve_phase_weighted(from,to,stats,bounds,u,weight):solver.solve_phase(from,to,stats,bounds,u,error,INF,memo);if(cache)cache->put(key,delay);}
        if(delay>=INF)throw std::runtime_error("Unreachable query");
        out.write(s.data(),s.size());out.put(',');out.write(t.data(),t.size());out.put(',');char digits[32];auto end=std::to_chars(digits,digits+sizeof(digits),delay);if(end.ec!=std::errc())throw std::runtime_error("Delay formatting failed");out.write(digits,end.ptr-digits);out.put('\n');++rows;
        if(cert.is_open())cert<<rows<<','<<stats.lower<<','<<stats.upper<<','<<stats.settled<<','<<stats.relaxations<<'\n';
        if(progress && rows%1000==0)std::cerr<<"progress="<<rows<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
    }
    out.flush();if(cert.is_open())cert.flush();if(in.bad() || !out || (cert.is_open() && !cert))throw std::runtime_error("CSV I/O failure");
    std::cerr<<"rows="<<rows<<" cpu_seconds="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<" initialization_seconds="<<initialization<<" arch_sha256="<<archdata::HASH<<'\n';if(cache)std::cerr<<"cache_hits="<<cache->hits<<" cache_misses="<<cache->misses<<'\n';
 }catch(const std::exception& e){std::cerr<<"error: "<<e.what()<<'\n';return 1;}
}
