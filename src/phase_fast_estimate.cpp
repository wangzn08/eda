// Experimental fast approximate profiles: periodic bounds, compact residuals, templates.
#include "routing_search.hpp"
#include "phase_required_bound.hpp"
#include "periodic_dense_model.hpp"
#include "fast_residual_model.hpp"

#include <ctime>
#include <fstream>
#include <iostream>
#include <memory>
#include <filesystem>
std::string_view strip(std::string_view s) {
    auto a=s.find_first_not_of(" \r\n\t"),b=s.find_last_not_of(" \r\n\t");return a==s.npos?std::string_view{}:s.substr(a,b-a+1);
}
// Endpoint expansion is exact; only the interior is relaxed to the periodic graph.
Distance direct_lower(const Graph& graph,const PhaseLowerBound& bounds,const PhaseRequiredBound* required,Node source,Node target) {
    if(source==target)return 0;
    Node site=source/archdata::P;int port=source%archdata::P,tp=target%archdata::P;
    auto b=archdata::SITES[target/archdata::P];Distance best=INF;
    auto bound=[&](archdata::XY a,int p){return required?required->lower(a,p,b,tp,bounds):bounds.lower(a,p,b,tp);};
    if(site==target/archdata::P)for(auto e:graph.local_out(port))if(e.port==tp)best=std::min(best,Distance(e.delay));
    auto after_net=[&](int ni,Distance cost){auto m=graph.net_move(site,ni,false);if(m.site!=NONE)best=std::min(best,cost+m.delay+archdata::NETS[ni].delay+bound(archdata::SITES[m.site],archdata::NETS[ni].to));};
    if(bounds.compact_input(port))best=std::min(best,bound(archdata::SITES[site],port));
    else if(graph.net_out(port)>=0)after_net(graph.net_out(port),0);
    else for(auto e:graph.local_out(port))if(graph.net_out(e.port)>=0)after_net(graph.net_out(e.port),e.delay);
    return best;
}
int main(int argc,char** argv) {
 try {
    auto directory=std::filesystem::absolute(argv[0]).parent_path();
    std::string input,output,phase,required_path,dense_path,conditioned_path,residual_path;
    if(std::filesystem::exists(directory/"phase-bounds.bin"))phase=(directory/"phase-bounds.bin").string();
    if(std::filesystem::exists(directory/"residual.bin"))residual_path=(directory/"residual.bin").string();
    unsigned trees=256;bool use_cache=false,progress=false;
    for(int i=1;i<argc;++i){std::string arg=argv[i];
        if(arg=="--help"){std::cout<<"phase_fast_estimate -in requests.csv -out result.csv [--dense-model file [--conditioned-model file]] [--phase-bounds file [--required-phase file]] [--residual-model file --trees count (phase bounds required)] [--cache] [--no-cache] [--progress]\nExperimental approximate predictor; no error certificates.\n";return 0;}
        if(arg=="--cache"){use_cache=true;continue;}if(arg=="--no-cache"){use_cache=false;continue;}if(arg=="--progress"){progress=true;continue;}
        if(i+1==argc)throw std::runtime_error("Missing argument");
        if(arg=="-in")input=argv[++i];else if(arg=="-out")output=argv[++i];else if(arg=="--residual-model")residual_path=argv[++i];else if(arg=="--trees")trees=std::stoul(argv[++i]);else if(arg=="--phase-bounds")phase=argv[++i];else if(arg=="--required-phase")required_path=argv[++i];else if(arg=="--dense-model")dense_path=argv[++i];else if(arg=="--conditioned-model")conditioned_path=argv[++i];else throw std::runtime_error("Unknown option");
    }
    if(input.empty() || output.empty() || (phase.empty() && dense_path.empty()) || (!required_path.empty() && phase.empty()) || (!conditioned_path.empty() && dense_path.empty()) || (!residual_path.empty() && (phase.empty() || !dense_path.empty())))throw std::runtime_error("Invalid inputs or model dependencies");
    auto normalized=[](const std::string&p){return std::filesystem::weakly_canonical(std::filesystem::absolute(p));};
    for(auto&path:{input,phase,required_path,dense_path,conditioned_path,residual_path})if(!path.empty() && normalized(output)==normalized(path))throw std::runtime_error("Output must be distinct from inputs/assets");
    auto begin=std::clock();std::unique_ptr<PhaseLowerBound>bounds;if(!phase.empty())bounds=std::make_unique<PhaseLowerBound>(phase);
    std::unique_ptr<PhaseRequiredBound>required;if(!required_path.empty())required=std::make_unique<PhaseRequiredBound>(required_path);
    Graph graph;std::unique_ptr<PeriodicDenseModel>dense;if(!dense_path.empty())dense=std::make_unique<PeriodicDenseModel>(dense_path);if(!conditioned_path.empty())dense->load_conditioned(conditioned_path);FastPinParser parser;
    std::unique_ptr<FastResidualModel>residual;if(!residual_path.empty())residual=std::make_unique<FastResidualModel>(residual_path,trees);
    double init=double(std::clock()-begin)/CLOCKS_PER_SEC;
    std::unique_ptr<PredictionCache>cache;if(use_cache)cache=std::make_unique<PredictionCache>();
    std::ifstream in(input);std::ofstream out(output);std::vector<char>buffer(1<<20);out.rdbuf()->pubsetbuf(buffer.data(),buffer.size());
    std::string line;if(!in || !out || !std::getline(in,line) || strip(line)!="From,To")throw std::runtime_error("Input header must be From,To");
    out<<"From,To,delay\n";uint64_t rows=0;
    while(std::getline(in,line)){auto text=strip(line);if(text.empty())continue;auto comma=text.find(',');if(comma==text.npos || text.find(',',comma+1)!=text.npos)throw std::runtime_error("Invalid request row");
        auto s=strip(text.substr(0,comma)),t=strip(text.substr(comma+1));Node from=parser.pin(s),to=parser.pin(t);Distance delay=INF;uint64_t key=(uint64_t(from)<<32)|to;
        if(!cache || !cache->get(key,delay)){delay=dense?dense->predict(graph,from,to):direct_lower(graph,*bounds,required.get(),from,to);if(residual)delay=residual->predict(from,to,delay,*bounds);if(cache)cache->put(key,delay);}
        if(delay>=INF)throw std::runtime_error("Unreachable query");
        out.write(s.data(),s.size());out.put(',');out.write(t.data(),t.size());out.put(',');char digits[32];auto end=std::to_chars(digits,digits+sizeof(digits),delay);if(end.ec!=std::errc())throw std::runtime_error("Delay formatting failed");out.write(digits,end.ptr-digits);out.put('\n');++rows;
        if(progress && rows%100000==0)std::cerr<<"progress="<<rows<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
    }
    out.flush();if(in.bad() || !out)throw std::runtime_error("CSV I/O failure");
    std::cerr<<"rows="<<rows<<" cpu_seconds="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<" initialization_seconds="<<init<<" arch_sha256="<<archdata::HASH<<'\n';if(cache)std::cerr<<"cache_hits="<<cache->hits<<" cache_misses="<<cache->misses<<'\n';
 }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<'\n';return 1;}
}
