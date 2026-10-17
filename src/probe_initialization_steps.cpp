#include "core_template_model.hpp"
#include <filesystem>
#include <ctime>
#include <iostream>
#define STEP(expr) do{auto start=std::clock();expr;std::cerr<<#expr<<" cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';}while(false)
int main(int argc,char**argv){try{if(argc!=2)throw std::runtime_error("folder");std::filesystem::path p=argv[1];auto f=[&](const char*n){return(p/n).string();};auto start=std::clock();Graph graph;std::cerr<<"Graph cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';start=std::clock();CoreTemplateModel model(f("core-template.bin"),false,0,0,f("vertical-transients.bin"),UINT_MAX,f("horizontal-transients.bin"),f("vertical-far-delta.bin"),true,f("joint-interaction.bin"));std::cerr<<"Constructor cpu="<<double(std::clock()-start)/CLOCKS_PER_SEC<<'\n';STEP(model.enable_joint_layout());STEP(model.enable_short_vertical_layout());STEP(model.enable_corridor_hubs(1));STEP(model.enable_horizontal_layout());STEP(model.enable_terminal_hints(1,true));STEP(model.enable_horizontal_hints(f("horizontal-hints.bin")));STEP(model.enable_source_hints(graph,8,f("source-hints.bin")));}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
