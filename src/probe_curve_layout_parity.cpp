// Native numeric parity probe for research asset layouts.
#include "near_response_curve_model.hpp"
#include <iostream>
#include <random>
int main(int argc,char**argv){try{if(argc<3)throw std::runtime_error("reference and candidate assets required");NearResponseCurveModel reference(argv[1]);for(int a=2;a<argc;++a){NearResponseCurveModel candidate(argv[a]);std::mt19937 random(20261007);constexpr unsigned samples=250000;for(unsigned k=0;k<samples;++k){unsigned s=random()%160,t=random()%160;int x=int(random()%59)-29,y=int(96+(random()%40)*12+random()%12);if(random()&1)y=-y;if(reference.cost(s,t,x,y)!=candidate.cost(s,t,x,y))throw std::runtime_error("native curve layout disagreement");}std::cout<<"{\"asset\":\""<<argv[a]<<"\",\"samples\":"<<samples<<",\"exact_match\":true}\n";}}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
