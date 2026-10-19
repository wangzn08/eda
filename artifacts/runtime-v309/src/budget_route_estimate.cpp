// Tiny-correction front end over the V158 periodic min-plus route model.
#include "core_template_model.hpp"
#include "buffered_csv_reader.hpp"
#include "buffered_csv_writer.hpp"
#include <filesystem>
#include <iomanip>
#ifdef BUDGET_RESIDUAL_HEADER
#include BUDGET_RESIDUAL_HEADER
#else
static int budget_correct(Node,Node,int base){return base;}
#endif
#ifndef BUDGET_SOURCE_HINTS
#define BUDGET_SOURCE_HINTS 8
#endif
#ifndef CORE_BATCH_SIZE
#define CORE_BATCH_SIZE 16
#endif
static std::string_view budget_trim(std::string_view s){
 auto space=[](char c){return c==' '||c=='\r'||c=='\n'||c=='\t';};
 while(!s.empty()&&space(s.front()))s.remove_prefix(1);
 while(!s.empty()&&space(s.back()))s.remove_suffix(1);return s;
}
int main(int argc,char**argv){try{
 std::string input,output;for(int i=1;i<argc;++i){std::string a=argv[i];if(i+1==argc)throw std::runtime_error("Missing argument");if(a=="-in")input=argv[++i];else if(a=="-out")output=argv[++i];else throw std::runtime_error("Unknown argument");}if(input.empty()||output.empty())throw std::runtime_error("Input and output required");
 auto folder=std::filesystem::absolute(argv[0]).parent_path();auto normalized=[](const std::string&p){return std::filesystem::weakly_canonical(std::filesystem::absolute(p));};if(normalized(input)==normalized(output))throw std::runtime_error("Input/output collision");for(const char*asset:{"estimate","source-hints.bin","horizontal-hints.bin","core-template.bin","vertical-transients.bin","vertical-far-delta.bin","horizontal-transients.bin","joint-interaction.bin"})if(normalized(output)==normalized((folder/asset).string()))throw std::runtime_error("Asset/output collision");
 auto asset=[&](const char*name){return (folder/name).string();};auto start=std::clock();Graph graph;
 CoreTemplateModel predictor(asset("core-template.bin"),false,0,0,asset("vertical-transients.bin"),UINT_MAX,asset("horizontal-transients.bin"),asset("vertical-far-delta.bin"),true,asset("joint-interaction.bin"));
 predictor.enable_joint_layout();predictor.enable_short_vertical_layout();predictor.enable_corridor_hubs(1);predictor.enable_horizontal_layout();predictor.enable_terminal_hints(1,true);predictor.enable_horizontal_hints(asset("horizontal-hints.bin"));predictor.enable_source_hints(graph,BUDGET_SOURCE_HINTS,asset("source-hints.bin"));
 predictor.validate_periodic_specialization();
 FastPinParser parser;parser.enable_scan_coordinates();parser.enable_packed_port_index();double init=double(std::clock()-start)/CLOCKS_PER_SEC;
 BufferedCsvReader reader(input);BufferedCsvWriter writer(output);std::string_view line;if(!reader.next(line)||budget_trim(line)!="From,To")throw std::runtime_error("CSV header");
 struct Pending{std::string_view from,to;Node source,target;CoreTemplateModel::PreparedRequest request;};std::array<Pending,CORE_BATCH_SIZE>pending;unsigned used=0;uint64_t rows=0;
 auto flush=[&](){
  for(unsigned i=0;i<used;++i)predictor.prefetch_source_mask(pending[i].source,pending[i].target);
  for(unsigned i=0;i<used;++i){auto&r=pending[i];predictor.prepare_request(graph,r.source,r.target,r.request);predictor.prefetch_prepared(r.request,false);}
  for(unsigned i=0;i<used;++i)predictor.prefetch_prepared(pending[i].request,true);
  for(unsigned i=0;i<used;++i){auto&r=pending[i];auto base=predictor.predict_periodic_prepared(graph,r.request);if(base>=INF||base>1000000000)throw std::runtime_error("Unreachable query");int value=budget_correct(r.source,r.target,int(base));if(r.to.data()==r.from.data()+r.from.size()+1)writer.row_pair({r.from.data(),r.from.size()+r.to.size()+1},value);else writer.row(r.from,r.to,value);++rows;}used=0;
 };reader.set_before_refill([&](){if(used)flush();});
 while(reader.next(line)){line=budget_trim(line);if(line.empty())continue;auto c=line.find(',');if(c==line.npos||line.find(',',c+1)!=line.npos)throw std::runtime_error("CSV row");auto from=budget_trim(line.substr(0,c)),to=budget_trim(line.substr(c+1));auto&r=pending[used++];r.from=from;r.to=to;r.source=parser.pin(from);r.target=parser.pin(to);if(used==pending.size())flush();}
 if(used)flush();writer.finish();std::cerr<<std::setprecision(12)<<"rows="<<rows<<" cpu_seconds="<<double(std::clock()-start)/CLOCKS_PER_SEC<<" initialization_seconds="<<init<<" arch_sha256="<<archdata::HASH<<'\n';
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<'\n';return 1;}}
