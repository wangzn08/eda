#pragma once
#include "routing_search.hpp"
inline Distance direct_phase_lower(const Graph&graph,const PhaseLowerBound&bounds,Node source,Node target){
 if(source==target)return 0;Node site=source/496;int port=source%496,tp=target%496;auto b=archdata::SITES[target/496];Distance best=INF;
 if(site==target/496)for(auto e:graph.local_out(port))if(e.port==tp)best=std::min(best,Distance(e.delay));
 auto after_net=[&](int ni,Distance cost){auto m=graph.net_move(site,ni,false);if(m.site!=NONE)best=std::min(best,cost+m.delay+archdata::NETS[ni].delay+bounds.lower(archdata::SITES[m.site],archdata::NETS[ni].to,b,tp));};
 if(bounds.compact_input(port))best=std::min(best,bounds.lower(archdata::SITES[site],port,b,tp));else if(graph.net_out(port)>=0)after_net(graph.net_out(port),0);else for(auto e:graph.local_out(port))if(graph.net_out(e.port)>=0)after_net(graph.net_out(e.port),e.delay);
 return best;
}
