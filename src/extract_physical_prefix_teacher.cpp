// Shared-initialization research comparison, no result caching; not final timing.
#include "core_template_model.hpp"
#include "buffered_csv_reader.hpp"
#include "buffered_csv_writer.hpp"
#include <filesystem>
#include <ctime>
std::string_view trim135(std::string_view s){auto a=s.find_first_not_of(" \r\n\t"),b=s.find_last_not_of(" \r\n\t");return a==s.npos?std::string_view{}:s.substr(a,b-a+1);}
int main(int argc,char**argv){try{if(argc!=4)throw std::runtime_error("asset folder, request file, output folder required");auto folder=std::filesystem::path(argv[1]);auto file=[&](const char*n){return (folder/n).string();};auto start=std::clock();Graph graph;CoreTemplateModel model(file("core-template.bin"),false,0,0,file("vertical-transients.bin"),UINT_MAX,file("horizontal-transients.bin"),file("vertical-far-delta.bin"),true,file("joint-interaction.bin"));model.enable_near_response_curves("out/v172/curves-layout-15.bin");model.enable_joint_layout();model.enable_short_vertical_layout();model.enable_corridor_hubs(1);model.enable_horizontal_layout();model.enable_terminal_hints(1,true);model.enable_horizontal_hints();model.enable_adaptive_sources(36);model.enable_source_hints(graph,8);
#if CORE_PHYSICAL_PORTALS
model.enable_physical_portals("out/v140/portal.raw.bin");
#endif
double init=double(std::clock()-start)/CLOCKS_PER_SEC;std::cerr<<"init="<<init<<'\n';FastPinParser parser;parser.enable_scan_coordinates();parser.enable_packed_port_index();model.enable_corridor_hubs(8);model.set_physical_prefix(2,0);model.enable_adaptive_sources(10000);BufferedCsvWriter writer(argv[3]);auto begin=std::clock();BufferedCsvReader reader(argv[2]);std::string_view line;if(!reader.next(line)||trim135(line)!="From,To")throw std::runtime_error("header");size_t rows=0;while(reader.next(line)){line=trim135(line);if(line.empty())continue;auto c=line.find(',');if(c==line.npos)throw std::runtime_error("row");auto from=trim135(line.substr(0,c)),to=trim135(line.substr(c+1));writer.row(from,to,model.predict(graph,parser.pin(from),parser.pin(to)));++rows;}writer.finish();std::cerr<<"rows="<<rows<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
