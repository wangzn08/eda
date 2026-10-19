#include "runtime_route_model.hpp"
#include <tuple>
#include "endpoint_bellman_profile.hpp"
#include "buffered_csv_reader.hpp"
#include <filesystem>
int main(int argc,char**argv){try{
 if(argc<4||argc>5)throw std::runtime_error("asset directory, input CSV, feature output, optional selected mode required");
 auto start=std::clock();Graph graph;RuntimeRouteModel model(graph,argv[1]);EndpointBellmanProfile profile(graph);
 FastPinParser parser;parser.enable_scan_coordinates();parser.enable_packed_port_index();
 double init=double(std::clock()-start)/CLOCKS_PER_SEC;BufferedCsvReader reader(argv[2]);std::string_view line;
 if(!reader.next(line)||line!="From,To")throw std::runtime_error("CSV header");
 std::ofstream output(argv[3],std::ios::binary);uint64_t rows=0;
 while(reader.next(line)){if(line.empty())continue;auto comma=line.find(',');auto to=line.substr(comma+1);if(!to.empty()&&to.back()=='\r')to.remove_suffix(1);
  PreparedKernelRequest r;model.prepare(parser.pin(line.substr(0,comma)),parser.pin(to),r);model.prefetch(r);KernelTrace trace;int base=model.base(r,trace);
#if RUNTIME_PATH_ENVELOPE
  auto features=trace.envelope;
#else
  auto features=profile.evaluate(model,r,base,2,argc==5?&trace:nullptr,31,RUNTIME_ENDPOINT_SEEDS);
#endif
  output.write(reinterpret_cast<const char*>(&base),4);output.write(reinterpret_cast<const char*>(features.data()),sizeof features);++rows;
  if(rows%100000==0)std::cerr<<"profile_rows="<<rows<<" cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';
 }
 if(!output)throw std::runtime_error("Feature output");std::cerr<<"rows="<<rows<<" initialization_seconds="<<init<<" cpu_seconds="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
