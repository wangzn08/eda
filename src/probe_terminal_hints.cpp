#include "core_template_model.hpp"
#include "buffered_csv_writer.hpp"
#include <ctime>
#include <iostream>
#include <fstream>
int main(){try{
 auto start=std::clock();Graph graph;CoreTemplateModel model("out/architecture-benchmark/core-template-xz6.bin",false,0,0,"out/architecture-benchmark/vertical-transients-xz.bin",UINT_MAX,"out/architecture-benchmark/horizontal-transients.bin","out/architecture-benchmark/vertical-distant-delta-xz6.bin",true,"out/architecture-benchmark/joint-transient-xz6.bin");model.enable_joint_layout();model.enable_short_vertical_layout();model.enable_corridor_hubs(1);model.enable_terminal_hints(2);double init=double(std::clock()-start)/CLOCKS_PER_SEC;FastPinParser parser;
 for(unsigned count:{1u,2u}){model.set_terminal_hint_count(count);
  for(const char*split:{"validation","speed1m"}){std::string input=std::string(split)=="validation"?"out/evaluation/validation.request.csv":"out/v99/speed1m.request.csv";std::string output="out/v104/"+std::string(split)+"-k"+std::to_string(count)+".csv";auto begin=std::clock();std::ifstream in(input);BufferedCsvWriter writer(output);std::string line;std::getline(in,line);uint64_t rows=0;
   while(std::getline(in,line)){auto c=line.find(',');if(c==line.npos)throw std::runtime_error("CSV split");std::string_view s(line.data(),c),t(line.data()+c+1,line.size()-c-1);while(!t.empty() && (t.back()=='\r' || t.back()==' '))t.remove_suffix(1);Node a=parser.pin(s),b=parser.pin(t);auto v=model.predict(graph,a,b);if(v>=INF)throw std::runtime_error("Unreachable");writer.row(s,t,v);++rows;}writer.finish();if(in.bad())throw std::runtime_error("CSV read");double query=double(std::clock()-begin)/CLOCKS_PER_SEC;std::cout<<"case="<<split<<" candidates="<<count<<" rows="<<rows<<" initialization_seconds="<<init<<" query_cpu_seconds="<<query<<'\n'<<std::flush;
  }
 }
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
