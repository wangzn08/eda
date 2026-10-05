#include "routing_search.hpp"
#include <fstream>
#include <iostream>
#include <ctime>
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Expected request and output paths");
 Graph graph;CompactSolver solver(graph);FastPinParser parser;std::ifstream in(argv[1]);std::ofstream out(argv[2]);std::string line;std::getline(in,line);out<<"row,delay,step,x,y,port\n";unsigned row=0;auto begin=std::clock();
 while(std::getline(in,line)){auto comma=line.find(',');if(comma==line.npos)throw std::runtime_error("Invalid row");auto target=line.substr(comma+1);if(!target.empty() && target.back()=='\r')target.pop_back();SearchStats stats;auto path=solver.trace(parser.pin(line.substr(0,comma)),parser.pin(target),stats);++row;unsigned step=0;for(auto state:path.states){auto xy=archdata::SITES[solver.trace_site(state)];out<<row<<','<<path.delay<<','<<step++<<','<<xy.x<<','<<xy.y<<','<<solver.trace_port(state)<<'\n';}std::cerr<<"row="<<row<<" states="<<path.states.size()<<" settled="<<stats.settled<<'\n';}
 out.flush();if(in.bad() || !out)throw std::runtime_error("I/O failed");std::cerr<<"cpu_seconds="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
