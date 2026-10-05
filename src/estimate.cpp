#include "architecture_data.hpp"
#include "lookup_model.hpp"
#include "spatial_model.hpp"
#include "port_model.hpp"
#include "source_x_model.hpp"
#include "target_x_model.hpp"
#include "dx_model.hpp"
#include "route_v3_model.hpp"
#include "forced_route_model.hpp"
#include "route_v3_final_model.hpp"
#include "v4_tree_model.hpp"
#include "v4_table_model.hpp"
#include "v4_horizontal_model.hpp"
#include "v5_geometry_model.hpp"
#include "v6_pair_model.hpp"
#include "v7_tree_model.hpp"
#include "v9_tree_model.hpp"
#include "v10_tree_model.hpp"
#include "v14_tree_model.hpp"
#include "v19_tree_model.hpp"
#include "cycle_path_oracle.hpp"
#include "macro_path_oracle.hpp"
#include "phase_route_model.hpp"
#include "phase_lower_bound.hpp"
#include "routing_search.hpp"
#include <cstring>
#include "local_path_oracle.hpp"
#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>


// Offline-fitted, constant-time approximate oracle. All inputs are public
// architecture constants and the request endpoints; no labels are read here.
Distance lookup_delay(Node source,Node target) {
    if(source==target) return 0;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=b.x-a.x,dy=b.y-a.y;
    int sx=(dx>0)-(dx<0),sy=(dy>0)-(dy<0);
    size_t key=(((sx+1)*3+(sy+1))*15+std::abs(dx)/8)*35+std::abs(dy)/16;
    double estimate=lookup_model::intercept+lookup_model::ax*std::abs(dx)
        +lookup_model::ay*std::abs(dy)+lookup_model::residual[key]
        +lookup_model::source[source%archdata::P]+lookup_model::target[target%archdata::P];
    estimate=std::max(0.0,std::nearbyint(estimate));
    for(const auto& line:archdata::LINES) {
        int u=line.vertical?a.x:a.y,v=line.vertical?b.x:b.y;
        if(std::min(u,v)<=line.site && line.site<std::max(u,v)) estimate+=lookup_model::line[line.id];
    }
    for(const auto& block:archdata::BLOCKS) {
        if(std::max(a.x,b.x)>=block.left && std::min(a.x,b.x)<=block.right
           && std::max(a.y,b.y)>=block.lower && std::min(a.y,b.y)<=block.upper)
            estimate+=lookup_model::block[block.id];
    }
    return static_cast<Distance>(std::max(0.0,std::nearbyint(estimate)));
}

Distance spatial_delay(Node source,Node target) {
    Distance base=lookup_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int xsign=(b.x>a.x)-(b.x<a.x),ysign=(b.y>a.y)-(b.y<a.y);
    const size_t xkey=((a.x/10)*12+(b.x/10))*3+ysign+1;
    const size_t ykey=((a.y/50)*11+(b.y/50))*3+xsign+1;
    double estimate=base+spatial_model::x_pair[xkey]+spatial_model::y_pair[ykey];
    return static_cast<Distance>(std::max(0.0,std::nearbyint(estimate)));
}

Distance port_delay(Node source,Node target) {
    Distance base=spatial_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=(b.x>a.x)-(b.x<a.x),dy=(b.y>a.y)-(b.y<a.y);
    int from=port_model::family[source%archdata::P];
    int to=port_model::family[target%archdata::P];
    size_t key=((from*port_model::FAMILIES+to)*3+dx+1)*3+dy+1;
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+port_model::residual[key])));
}

Distance source_x_delay(Node source,Node target) {
    Distance base=port_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=(b.x>a.x)-(b.x<a.x),dy=(b.y>a.y)-(b.y<a.y);
    int from=port_model::family[source%archdata::P];
    size_t key=((from*120+a.x)*3+dx+1)*3+dy+1;
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+source_x_model::residual[key])));
}

Distance target_x_delay(Node source,Node target) {
    Distance base=source_x_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=(b.x>a.x)-(b.x<a.x),dy=(b.y>a.y)-(b.y<a.y);
    int to=port_model::family[target%archdata::P];
    size_t key=((to*120+b.x)*3+dx+1)*3+dy+1;
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+target_x_model::residual[key])));
}

Distance v2_delay(Node source,Node target) {
    Distance base=target_x_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=b.x-a.x,ysign=(b.y>a.y)-(b.y<a.y);
    size_t key=(dx+119)*3+ysign+1;
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+dx_model::residual[key])));
}
struct NetVectors {
    std::array<archdata::XY,archdata::P> first{},last{};
};
const NetVectors& endpoint_vectors() {
    static const NetVectors vectors=[] {
        NetVectors result;
        for(const auto& net:archdata::NETS) {
            const auto v=archdata::VECTORS[net.vector];
            result.first[net.from]=v;
            result.last[net.to]=v;
        }
        return result;
    }();
    return vectors;
}
Distance v3_delay(Node source,Node target) {
    Distance base=v2_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,dy=b.y-a.y;
    const int distance=std::abs(dx)+std::abs(dy);
    const int bucket=distance<16?0:distance<64?1:distance<256?2:3;
    const auto initial=[](char c){return c=='A'?0:c=='S'?1:c=='Z'?2:3;};
    int route=0,detour=0;
    if(std::min(a.x,b.x)<=89 && std::max(a.x,b.x)>=76) {
        const auto blocked=[](int y){return y<550 && y%100<50?y/100:-1;};
        int s=blocked(a.y),t=blocked(b.y);
        if(s>=0 || t>=0) {
            if(s!=t) route=1;
            else {
                route=2;
                int lower=s*100,upper=lower+49;
                int distance_to_edge=std::min(a.y-lower+b.y-lower+2,2*upper-a.y-b.y+2);
                detour=std::min(9,std::max(0,distance_to_edge/10));
            }
        }
    }
    size_t route_key=((((route*10+detour)*4+initial(archdata::PORTS[source%archdata::P][0]))*4
                       +initial(archdata::PORTS[target%archdata::P][0]))*4+bucket);
    double estimate=std::max(0.0,std::nearbyint(base+route_v3_model::route[route_key]));
    const int port=source%archdata::P;
    const auto v=endpoint_vectors().first[port];
    const int projection=v.x*dx+v.y*dy;
    const int momentum=(v.x || v.y)?(projection>0?1:projection<0?2:3):0;
    const int port_key=momentum?port:archdata::P;
    const int xsign=(dx>0)-(dx<0),ysign=(dy>0)-(dy<0);
    size_t momentum_key=((((port_key*4+momentum)*4+bucket)*3+xsign+1)*3+ysign+1);
    return static_cast<Distance>(std::max(0.0,std::nearbyint(estimate+route_v3_model::momentum[momentum_key])));
}
Distance v3_forced_delay(Node source,Node target) {
    Distance base=v3_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    int dx=b.x-a.x,dy=b.y-a.y;
    const auto& vectors=endpoint_vectors();
    const auto first=vectors.first[source%archdata::P];
    const auto last=vectors.last[target%archdata::P];
    const int direct=std::abs(dx)+std::abs(dy);
    const int forced=std::abs(first.x)+std::abs(first.y)+std::abs(last.x)+std::abs(last.y)
        +std::abs(dx-first.x-last.x)+std::abs(dy-first.y-last.y);
    const int detour=std::min(50,std::max(0,forced-direct));
    const int bucket=direct<16?0:direct<64?1:direct<256?2:3;
    const int s=first.x || first.y,t=last.x || last.y;
    size_t key=(((detour*4+bucket)*2+s)*2+t);
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+forced_route_model::residual[key])));
}
Distance v3_final_delay(Node source,Node target) {
    Distance base=v2_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,dy=b.y-a.y,direct=std::abs(dx)+std::abs(dy);
    const int bucket=direct<16?0:direct<64?1:direct<256?2:3;
    const auto initial=[](char c){return c=='A'?0:c=='S'?1:c=='Z'?2:3;};
    int route=0,detour=0;
    if(std::min(a.x,b.x)<=89 && std::max(a.x,b.x)>=76) {
        const auto blocked=[](int y){return y<550 && y%100<50?y/100:-1;};
        int s=blocked(a.y),t=blocked(b.y);
        if(s>=0 || t>=0) {
            if(s!=t) route=1;
            else {
                route=2;
                int lower=s*100,upper=lower+49;
                int distance_to_edge=std::min(a.y-lower+b.y-lower+2,2*upper-a.y-b.y+2);
                detour=std::min(9,std::max(0,distance_to_edge/10));
            }
        }
    }
    size_t route_key=((((route*10+detour)*4+initial(archdata::PORTS[source%archdata::P][0]))*4
                       +initial(archdata::PORTS[target%archdata::P][0]))*4+bucket);
    double estimate=std::max(0.0,std::nearbyint(base+route_v3_final_model::route[route_key]));
    const auto& vectors=endpoint_vectors();
    const auto first=vectors.first[source%archdata::P];
    const auto last=vectors.last[target%archdata::P];
    const int forced=std::abs(first.x)+std::abs(first.y)+std::abs(last.x)+std::abs(last.y)
        +std::abs(dx-first.x-last.x)+std::abs(dy-first.y-last.y);
    const int extra=std::min(50,std::max(0,forced-direct));
    const int source_fixed=first.x || first.y,target_fixed=last.x || last.y;
    size_t forced_key=(((extra*4+bucket)*2+source_fixed)*2+target_fixed);
    estimate=std::max(0.0,std::nearbyint(estimate+route_v3_final_model::forced[forced_key]));
    const int projection=first.x*dx+first.y*dy;
    const int momentum=source_fixed?(projection>0?1:projection<0?2:3):0;
    const int port_key=momentum?source%archdata::P:archdata::P;
    const int xsign=(dx>0)-(dx<0),ysign=(dy>0)-(dy<0);
    size_t momentum_key=((((port_key*4+momentum)*4+bucket)*3+xsign+1)*3+ysign+1);
    return static_cast<Distance>(std::max(0.0,std::nearbyint(estimate+route_v3_final_model::momentum[momentum_key])));
}
Distance v4_tree_delay(Node source,Node target) {
    Distance base=v3_final_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,dy=b.y-a.y,direct=std::abs(dx)+std::abs(dy);
    const auto& vectors=endpoint_vectors();
    const auto first=vectors.first[source%archdata::P],last=vectors.last[target%archdata::P];
    const int forced=std::abs(first.x)+std::abs(first.y)+std::abs(last.x)+std::abs(last.y)
        +std::abs(dx-first.x-last.x)+std::abs(dy-first.y-last.y);
    int route=0,route_detour=0;
    if(std::min(a.x,b.x)<=89 && std::max(a.x,b.x)>=76) {
        const auto blocked=[](int y){return y<550 && y%100<50?y/100:-1;};
        int s=blocked(a.y),t=blocked(b.y);
        if(s>=0 || t>=0) {
            if(s!=t) route=1;
            else {
                route=2;
                int lower=s*100,upper=lower+49;
                int distance_to_edge=std::min(a.y-lower+b.y-lower+2,2*upper-a.y-b.y+2);
                route_detour=std::min(9,std::max(0,distance_to_edge/10));
            }
        }
    }
    const int xmin=std::min(a.x,b.x),xmax=std::max(a.x,b.x);
    const int ymin=std::min(a.y,b.y),ymax=std::max(a.y,b.y);
    const auto& m=v4_tree_model::family;
    std::array<float,31> feature={
        float(a.x),float(a.y),float(b.x),float(b.y),float(dx),float(dy),
        float(std::abs(dx)),float(std::abs(dy)),float(direct),float(base),
        float(source%archdata::P),float(target%archdata::P),
        float(m[source%archdata::P]),float(m[target%archdata::P]),
        float((dx>0)-(dx<0)),float((dy>0)-(dy<0)),
        float(a.x%10),float(b.x%10),float(a.y%12),float(b.y%12),
        float(v4_tree_model::x_gap_prefix[xmax]-v4_tree_model::x_gap_prefix[xmin]),
        float(v4_tree_model::y_gap_prefix[ymax]-v4_tree_model::y_gap_prefix[ymin]),
        float(route),float(route_detour),float(std::max(0,forced-direct)),
        float(first.x*dx+first.y*dy),float(last.x*dx+last.y*dy),
        float(first.x || first.y),float(last.x || last.y),
        float(a.y%100),float(b.y%100)};
    double correction=0.;
    for(uint32_t root:v4_tree_model::roots) {
        uint32_t node=root;
        while(v4_tree_model::nodes[node].feature!=65535) {
            const auto& branch=v4_tree_model::nodes[node];
            node=feature[branch.feature]<=branch.threshold?branch.left:branch.right;
        }
        correction+=v4_tree_model::nodes[node].value;
    }
    return static_cast<Distance>(std::max(0.0,std::nearbyint(double(base)*(1.0+correction))));
}
Distance v4_table_delay(Node source,Node target) {
    Distance base=v3_final_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,dy=b.y-a.y;
    const int xsign=(dx>0)-(dx<0),ysign=(dy>0)-(dy<0);
    const int bucket=std::abs(dy)/16;
    double estimate=std::max(0.0,std::nearbyint(base+v4_table_model::signed_dy_exact[(dy+549)*3+xsign+1]));
    estimate=std::max(0.0,std::nearbyint(estimate+v4_table_model::target_port_dy16
        [(target%archdata::P*35+bucket)*3+ysign+1]));
    estimate=std::max(0.0,std::nearbyint(estimate+v4_table_model::source_port_dy16
        [(source%archdata::P*35+bucket)*3+ysign+1]));
    return static_cast<Distance>(estimate);
}
Distance v4_horizontal_delay(Node source,Node target) {
    Distance base=v4_table_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,dy=b.y-a.y;
    const int xsign=(dx>0)-(dx<0),ysign=(dy>0)-(dy<0);
    double estimate=std::max(0.0,std::nearbyint(base+v4_horizontal_model::signed_dx_dybucket
        [((dx+119)*18+std::abs(dy)/32)*3+ysign+1]));
    estimate=std::max(0.0,std::nearbyint(estimate+v4_horizontal_model::target_port_dx8
        [(target%archdata::P*15+std::abs(dx)/8)*3+xsign+1]));
    estimate=std::max(0.0,std::nearbyint(estimate+v4_horizontal_model::source_port_dx8
        [(source%archdata::P*15+std::abs(dx)/8)*3+xsign+1]));
    return static_cast<Distance>(estimate);
}
Distance v5_geometry_delay(Node source,Node target) {
    Distance base=v4_horizontal_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,xsign=(dx>0)-(dx<0),bucket=std::abs(dx)/16;
    double estimate=std::max(0.0,std::nearbyint(base+
        v5_geometry_model::source_x_target_x[a.x*120+b.x]));
    estimate=std::max(0.0,std::nearbyint(estimate+
        v5_geometry_model::source_port_x[source%archdata::P*120+a.x]));
    estimate=std::max(0.0,std::nearbyint(estimate+
        v5_geometry_model::source_yphase_dx16[((a.y%100/5)*8+bucket)*3+xsign+1]));
    estimate=std::max(0.0,std::nearbyint(estimate+
        v5_geometry_model::target_yphase_dx16[((b.y%100/5)*8+bucket)*3+xsign+1]));
    estimate=std::max(0.0,std::nearbyint(estimate+
        v5_geometry_model::target_x_dx16[(b.x*8+bucket)*3+xsign+1]));
    return static_cast<Distance>(estimate);
}
Distance v5_geometry_fused_delay(Node source,Node target) {
    Distance base=v4_horizontal_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,xsign=(dx>0)-(dx<0),bucket=std::abs(dx)/16;
    const double correction=
        v5_geometry_model::source_x_target_x[a.x*120+b.x]+
        v5_geometry_model::source_port_x[source%archdata::P*120+a.x]+
        v5_geometry_model::source_yphase_dx16[((a.y%100/5)*8+bucket)*3+xsign+1]+
        v5_geometry_model::target_yphase_dx16[((b.y%100/5)*8+bucket)*3+xsign+1]+
        v5_geometry_model::target_x_dx16[(b.x*8+bucket)*3+xsign+1];
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+correction)));
}
Distance v6_pair_delay(Node source,Node target) {
    Distance base=v5_geometry_fused_delay(source,target);
    if(source==target) return base;
    const unsigned source_port=source%archdata::P,target_port=target%archdata::P;
    const double correction=v6_pair_model::correction[source_port*archdata::P+target_port];
    return static_cast<Distance>(std::max(0.0,std::nearbyint(base+correction)));
}
Distance v7_tree_delay(Node source,Node target) {
    Distance base=v6_pair_delay(source,target);
    if(source==target) return base;
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,dy=b.y-a.y,direct=std::abs(dx)+std::abs(dy);
    const auto& vectors=endpoint_vectors();
    const auto first=vectors.first[source%archdata::P],last=vectors.last[target%archdata::P];
    const int forced=std::abs(first.x)+std::abs(first.y)+std::abs(last.x)+std::abs(last.y)
        +std::abs(dx-first.x-last.x)+std::abs(dy-first.y-last.y);
    int route=0,route_detour=0;
    if(std::min(a.x,b.x)<=89 && std::max(a.x,b.x)>=76) {
        const auto blocked=[](int y){return y<550 && y%100<50?y/100:-1;};
        int s=blocked(a.y),t=blocked(b.y);
        if(s>=0 || t>=0) {
            if(s!=t) route=1;
            else {
                route=2;
                int lower=s*100,upper=lower+49;
                int distance_to_edge=std::min(a.y-lower+b.y-lower+2,2*upper-a.y-b.y+2);
                route_detour=std::min(9,std::max(0,distance_to_edge/10));
            }
        }
    }
    const int xmin=std::min(a.x,b.x),xmax=std::max(a.x,b.x);
    const int ymin=std::min(a.y,b.y),ymax=std::max(a.y,b.y);
    const auto& m=v4_tree_model::family;
    std::array<float,31> feature={
        float(a.x),float(a.y),float(b.x),float(b.y),float(dx),float(dy),
        float(std::abs(dx)),float(std::abs(dy)),float(direct),float(base),
        float(source%archdata::P),float(target%archdata::P),
        float(m[source%archdata::P]),float(m[target%archdata::P]),
        float((dx>0)-(dx<0)),float((dy>0)-(dy<0)),
        float(a.x%10),float(b.x%10),float(a.y%12),float(b.y%12),
        float(v4_tree_model::x_gap_prefix[xmax]-v4_tree_model::x_gap_prefix[xmin]),
        float(v4_tree_model::y_gap_prefix[ymax]-v4_tree_model::y_gap_prefix[ymin]),
        float(route),float(route_detour),float(std::max(0,forced-direct)),
        float(first.x*dx+first.y*dy),float(last.x*dx+last.y*dy),
        float(first.x || first.y),float(last.x || last.y),
        float(a.y%100),float(b.y%100)};
    double correction=0.;
    for(uint32_t root:v7_tree_model::roots) {
        uint32_t node=root;
        while(v7_tree_model::nodes[node].feature!=65535) {
            const auto& branch=v7_tree_model::nodes[node];
            node=feature[branch.feature]<=branch.threshold?branch.left:branch.right;
        }
        correction+=v7_tree_model::nodes[node].value;
    }
    return static_cast<Distance>(std::max(0.0,std::nearbyint(double(base)*(1.0+v7_tree_model::blend*correction))));
}
std::array<float,73> topology_features(Node source,Node target) {
    Distance base=v6_pair_delay(source,target);
    const auto& a=archdata::SITES[source/archdata::P];
    const auto& b=archdata::SITES[target/archdata::P];
    const int dx=b.x-a.x,dy=b.y-a.y,direct=std::abs(dx)+std::abs(dy);
    const auto& vectors=endpoint_vectors();
    const auto first=vectors.first[source%archdata::P],last=vectors.last[target%archdata::P];
    const int forced=std::abs(first.x)+std::abs(first.y)+std::abs(last.x)+std::abs(last.y)
        +std::abs(dx-first.x-last.x)+std::abs(dy-first.y-last.y);
    int route=0,route_detour=0;
    if(std::min(a.x,b.x)<=89 && std::max(a.x,b.x)>=76) {
        const auto blocked=[](int y){return y<550 && y%100<50?y/100:-1;};
        int s=blocked(a.y),t=blocked(b.y);
        if(s>=0 || t>=0) {
            if(s!=t) route=1;
            else {
                route=2;
                int lower=s*100,upper=lower+49;
                int distance_to_edge=std::min(a.y-lower+b.y-lower+2,2*upper-a.y-b.y+2);
                route_detour=std::min(9,std::max(0,distance_to_edge/10));
            }
        }
    }
    const int xmin=std::min(a.x,b.x),xmax=std::max(a.x,b.x);
    const int ymin=std::min(a.y,b.y),ymax=std::max(a.y,b.y);
    const auto& m=v4_tree_model::family;
    std::array<float,73> feature={
        float(a.x),float(a.y),float(b.x),float(b.y),float(dx),float(dy),
        float(std::abs(dx)),float(std::abs(dy)),float(direct),float(base),
        float(source%archdata::P),float(target%archdata::P),
        float(m[source%archdata::P]),float(m[target%archdata::P]),
        float((dx>0)-(dx<0)),float((dy>0)-(dy<0)),
        float(a.x%10),float(b.x%10),float(a.y%12),float(b.y%12),
        float(v4_tree_model::x_gap_prefix[xmax]-v4_tree_model::x_gap_prefix[xmin]),
        float(v4_tree_model::y_gap_prefix[ymax]-v4_tree_model::y_gap_prefix[ymin]),
        float(route),float(route_detour),float(std::max(0,forced-direct)),
        float(first.x*dx+first.y*dy),float(last.x*dx+last.y*dy),
        float(first.x || first.y),float(last.x || last.y),
        float(a.y%100),float(b.y%100)};
    struct Topology {
        std::array<uint32_t,archdata::P*archdata::P> distance;
        std::array<std::array<uint32_t,4>,archdata::P> access,terminal,long_access,long_terminal;
    };
    static const Topology topology=[] {
        Topology result;result.distance.fill(10000000);
        for(int i=0;i<archdata::P;++i) result.distance[i*archdata::P+i]=0;
        for(const auto& arc:archdata::ARCS) {auto& d=result.distance[arc.from*archdata::P+arc.to];d=std::min(d,uint32_t(arc.delay));}
        for(const auto& net:archdata::NETS) {auto& d=result.distance[net.from*archdata::P+net.to];d=std::min(d,uint32_t(net.delay));}
        for(int k=0;k<archdata::P;++k) for(int i=0;i<archdata::P;++i) for(int j=0;j<archdata::P;++j) {
            auto& d=result.distance[i*archdata::P+j];d=std::min(d,result.distance[i*archdata::P+k]+result.distance[k*archdata::P+j]);
        }
        for(int i=0;i<archdata::P;++i) {result.access[i].fill(10000000);result.terminal[i].fill(10000000);result.long_access[i].fill(10000000);result.long_terminal[i].fill(10000000);}
        for(const auto& net:archdata::NETS) {
            auto v=archdata::VECTORS[net.vector];int direction=v.x>0?0:v.x<0?1:v.y>0?2:3;
            for(int i=0;i<archdata::P;++i) {
                auto ac=result.distance[i*archdata::P+net.from],te=result.distance[net.to*archdata::P+i];
                result.access[i][direction]=std::min(result.access[i][direction],ac);
                result.terminal[i][direction]=std::min(result.terminal[i][direction],te);
                if(std::abs(v.x)+std::abs(v.y)>=10) {
                    result.long_access[i][direction]=std::min(result.long_access[i][direction],ac);
                    result.long_terminal[i][direction]=std::min(result.long_terminal[i][direction],te);
                }
            }
        }
        return result;
    }();
    auto mod=[](int value,int divisor){return (value%divisor+divisor)%divisor;};
    int sp=source%archdata::P,tp=target%archdata::P,rx=dx-first.x-last.x,ry=dy-first.y-last.y;
    std::array<float,31> extra={float(first.x),float(first.y),float(last.x),float(last.y),
        float(rx),float(ry),float(std::abs(rx)),float(std::abs(ry)),float(mod(rx,12)),float(mod(ry,12)),
        float(mod(rx,4)),float(mod(ry,4)),float(sp%8),float(tp%8),float(topology.distance[sp*archdata::P+tp]),
        float(topology.access[sp][0]),float(topology.access[sp][1]),float(topology.access[sp][2]),float(topology.access[sp][3]),
        float(topology.terminal[tp][0]),float(topology.terminal[tp][1]),float(topology.terminal[tp][2]),float(topology.terminal[tp][3]),
        float(std::min(a.x,archdata::WIDTH-1-a.x)),float(std::min(a.y,archdata::HEIGHT-1-a.y)),
        float(std::min(b.x,archdata::WIDTH-1-b.x)),float(std::min(b.y,archdata::HEIGHT-1-b.y)),
        float(mod(a.x+first.x,10)),float(mod(b.x-last.x,10)),float(mod(a.y+first.y,12)),float(mod(b.y-last.y,12))};
    std::copy(extra.begin(),extra.end(),feature.begin()+31);
    std::array<float,11> wire={float(mod(rx,10)),float(std::abs(rx)%10),float(std::abs(ry)%12),
        float(topology.long_access[sp][0]),float(topology.long_access[sp][1]),float(topology.long_access[sp][2]),float(topology.long_access[sp][3]),
        float(topology.long_terminal[tp][0]),float(topology.long_terminal[tp][1]),float(topology.long_terminal[tp][2]),float(topology.long_terminal[tp][3])};
    std::copy(wire.begin(),wire.end(),feature.begin()+62);
    return feature;
}
Distance v9_tree_delay(Node source,Node target) {
    Distance base=v6_pair_delay(source,target);
    if(source==target) return base;
    auto feature=topology_features(source,target);
    double correction=0.;
    for(uint32_t root:v9_tree_model::roots) {
        uint32_t node=root;
        while(v9_tree_model::nodes[node].feature!=65535) {
            const auto& branch=v9_tree_model::nodes[node];
            node=feature[branch.feature]<=branch.threshold?branch.left:branch.right;
        }
        correction+=v9_tree_model::nodes[node].value;
    }
    return static_cast<Distance>(std::max(0.0,std::nearbyint(double(base)*(1.0+v9_tree_model::blend*correction))));
}
Distance v10_tree_delay(Node source,Node target) {
    Distance base=v6_pair_delay(source,target);
    if(source==target) return base;
    auto feature=topology_features(source,target);double correction=0.;
    for(uint32_t root:v10_tree_model::roots) {
        uint32_t node=root;
        while(v10_tree_model::code[node]!=255) {
            auto f=v10_tree_model::code[node];float threshold;
            std::memcpy(&threshold,v10_tree_model::code.data()+node+3,4);
            uint32_t right=v10_tree_model::code[node+1]|(uint32_t(v10_tree_model::code[node+2])<<8);
            node+=feature[f]<=threshold?7:right;
        }
        double value;std::memcpy(&value,v10_tree_model::code.data()+node+1,8);correction+=value;
    }
    return static_cast<Distance>(std::max(0.0,std::nearbyint(double(base)*(1.0+correction))));
}

Distance v14_tree_delay(Node source,Node target,Distance upper) {
    Distance base=v6_pair_delay(source,target);
    if(source==target) return base;
    auto original=topology_features(source,target);
    std::array<float,77> feature{};std::copy(original.begin(),original.end(),feature.begin());
    bool available=upper<INF;
    feature[73]=available?float(upper):0.f;feature[74]=available?1.f:0.f;
    feature[75]=available?float(double(upper)/std::max(1.0,double(base))):0.f;
    feature[76]=available?float(double(upper)-double(base)):0.f;
    double anchor=v14_tree_model::slack_anchor && available?double(upper):double(base);
    double correction=0.;
    for(uint32_t root:v14_tree_model::roots) {
        uint32_t node=root;
        while(v14_tree_model::code[node]!=255) {
            auto f=v14_tree_model::code[node];float threshold;
            std::memcpy(&threshold,v14_tree_model::code.data()+node+3,4);
            uint32_t right=v14_tree_model::code[node+1]|(uint32_t(v14_tree_model::code[node+2])<<8);
            node+=feature[f]<=threshold?7:right;
        }
        double value;std::memcpy(&value,v14_tree_model::code.data()+node+1,8);correction+=value;
    }
    return std::min(upper,static_cast<Distance>(std::max(0.0,std::nearbyint(anchor*(1.0+correction)))));
}

Distance v19_tree_delay(Node source,Node target,Distance upper) {
    Distance base=v6_pair_delay(source,target);
    if(source==target) return base;
    auto original=topology_features(source,target);
    std::array<float,77> feature{};std::copy(original.begin(),original.end(),feature.begin());
    bool available=upper<INF;
    feature[73]=available?float(upper):0.f;feature[74]=available?1.f:0.f;
    feature[75]=available?float(double(upper)/std::max(1.0,double(base))):0.f;
    feature[76]=available?float(double(upper)-double(base)):0.f;
    double anchor=v19_tree_model::slack_anchor && available?double(upper):double(base);
    double correction=0.;
    for(uint32_t root:v19_tree_model::roots) {
        uint32_t node=root;
        while(v19_tree_model::code[node]!=255) {
            auto f=v19_tree_model::code[node];float threshold;
            std::memcpy(&threshold,v19_tree_model::code.data()+node+3,4);
            uint32_t right=v19_tree_model::code[node+1]|(uint32_t(v19_tree_model::code[node+2])<<8);
            node+=feature[f]<=threshold?7:right;
        }
        double value;std::memcpy(&value,v19_tree_model::code.data()+node+1,8);correction+=value;
    }
    return std::min(upper,static_cast<Distance>(std::max(0.0,std::nearbyint(anchor*(1.0+correction)))));
}

class Solver {
    const Graph& graph;
    Frontier forward,backward;
public:
    explicit Solver(const Graph& g):graph(g),forward(g.nodes()),backward(g.nodes()) {}
    Distance solve(Node s,Node t,bool bidirectional,SearchStats& stats) {
        forward.reset(); backward.reset();
        if(s==t) return 0;
        forward.improve(s,0);
        if(!bidirectional) {
            while(!forward.empty()) {
                Node u=forward.pop(); ++stats.settled;
                if(u==t) return forward.get(u);
                graph.neighbors(u,false,[&](Node v,uint32_t weight) {
                    ++stats.relaxations; forward.improve(v,forward.get(u)+weight);
                });
            }
            return INF;
        }
        backward.improve(t,0);
        Distance best=INF;
        while(!forward.empty() && !backward.empty()) {
            if(forward.top()+backward.top()>=best) break;
            bool reverse=backward.top()<forward.top();
            Frontier& current=reverse?backward:forward;
            Frontier& other=reverse?forward:backward;
            Node u=current.pop(); ++stats.settled;
            Distance du=current.get(u);
            best=std::min(best,du+other.get(u));
            graph.neighbors(u,reverse,[&](Node v,uint32_t weight) {
                ++stats.relaxations;
                Distance dv=du+weight;
                current.improve(v,dv);
                best=std::min(best,dv+other.get(v));
            });
        }
        return best;
    }
};

// Arc edges always go Input -> Output; Net edges always Output -> Input.
// Interior vertices can therefore be reduced to 160 inter-SRB Input ports.
std::string trim(std::string s) {
    auto a=s.find_first_not_of(" \t\r\n"), b=s.find_last_not_of(" \t\r\n");
    return a==std::string::npos?"":s.substr(a,b-a+1);
}

std::string_view trim_view(std::string_view s) {
    auto first=s.find_first_not_of(" \t\r\n"),last=s.find_last_not_of(" \t\r\n");
    return first==s.npos?std::string_view{}:s.substr(first,last-first+1);
}

int main(int argc,char** argv) {
    try {
        std::string input,output,stats_path,trace_path,certificate_path,phase_bounds_path,oracle_path,cycle_path,neural_path,neural_second_path,algorithm="v6-pair";
        bool cache_enabled=true,cycle_extra_hops=false,exact_astar=false,balanced_astar=false,progress=false;unsigned macro_budget=0,exact_short_distance=0;double neural_second_weight=.25,exact_uncertainty=0,certified_relative_error=0;uint64_t exact_short_queries=0,exact_uncertain_queries=0;
        for(int i=1;i<argc;++i) {
            std::string arg=argv[i];
            if(arg=="--help") {
                std::cout<<"estimate -in requests.csv -out results.csv [--algorithm bidirectional|dijkstra|compressed|phase-certified|approximate|spatial|port|source-x|target-x|v2|v3|v3-forced|v3-final|v4-tree|v4-table|v4-horizontal|v5-geometry|v5-geometry-fused|v6-pair|v7-tree|v9-tree|v10-tree|v14-tree|v19-tree] [--local-oracle dictionary.bin] [--cycle-oracle tail.bin] [--neural-model model.bin] [--neural-model-second model.bin] [--neural-second-weight value] [--macro-budget nodes] [--cycle-extra-hops] [--no-cache] [--exact-short-distance cells] [--exact-uncertainty fraction] [--exact-astar] [--balanced-astar] [--certified-relative-error fraction] [--phase-bounds dictionary.bin] [--progress] [--certificate bounds.csv (certified mode, no-cache)] [--stats stats.csv] [--trace trace.csv (compressed only)]\n";return 0;
            }
            if(arg=="--progress") {progress=true;continue;}
            if(arg=="--balanced-astar") {balanced_astar=true;continue;}
            if(arg=="--exact-astar") {exact_astar=true;continue;}
            if(arg=="--cycle-extra-hops") {cycle_extra_hops=true;continue;}
            if(arg=="--no-cache") {cache_enabled=false;continue;}
            if(i+1>=argc) throw std::runtime_error("Missing argument value");
            if(arg=="-in") input=argv[++i];
            else if(arg=="-out") output=argv[++i];
            else if(arg=="--stats") stats_path=argv[++i];
            else if(arg=="--certificate") certificate_path=argv[++i];
            else if(arg=="--trace") trace_path=argv[++i];
            else if(arg=="--exact-short-distance") exact_short_distance=std::stoul(argv[++i]);
            else if(arg=="--phase-bounds") phase_bounds_path=argv[++i];
            else if(arg=="--certified-relative-error") certified_relative_error=std::stod(argv[++i]);
            else if(arg=="--exact-uncertainty") exact_uncertainty=std::stod(argv[++i]);
            else if(arg=="--neural-model-second") neural_second_path=argv[++i];
            else if(arg=="--neural-second-weight") neural_second_weight=std::stod(argv[++i]);
            else if(arg=="--neural-model") neural_path=argv[++i];
            else if(arg=="--macro-budget") macro_budget=std::stoul(argv[++i]);
            else if(arg=="--cycle-oracle") cycle_path=argv[++i];
            else if(arg=="--local-oracle") oracle_path=argv[++i];
            else if(arg=="--algorithm") algorithm=argv[++i];
            else throw std::runtime_error("Unknown option: "+arg);
        }
        if(input.empty() || output.empty() || input==output) throw std::runtime_error("Provide distinct -in and -out files");
        if(!stats_path.empty() && (stats_path==input || stats_path==output)) throw std::runtime_error("Stats file must differ from input/output");
        if(!trace_path.empty() && (algorithm!="compressed" || trace_path==input || trace_path==output || trace_path==stats_path))
            throw std::runtime_error("Trace requires compressed algorithm and a distinct file");
        if(algorithm!="bidirectional" && algorithm!="dijkstra" && algorithm!="compressed" && algorithm!="phase-certified" && algorithm!="approximate" && algorithm!="spatial" && algorithm!="port" && algorithm!="source-x" && algorithm!="target-x" && algorithm!="v2" && algorithm!="v3" && algorithm!="v3-forced" && algorithm!="v3-final" && algorithm!="v4-tree" && algorithm!="v4-table" && algorithm!="v4-horizontal" && algorithm!="v5-geometry" && algorithm!="v5-geometry-fused" && algorithm!="v6-pair" && algorithm!="v7-tree" && algorithm!="v9-tree" && algorithm!="v10-tree" && algorithm!="v14-tree" && algorithm!="v19-tree") throw std::runtime_error("Unknown algorithm");
        std::ifstream in(input);
        if(!in) throw std::runtime_error("Cannot open input");
        std::string header;
        std::getline(in,header);
        if(trim(header)!="From,To") throw std::runtime_error("Expected input header From,To (no golden column)");
        std::vector<char> output_buffer(1<<20);
        std::ofstream out, stats, trace, certificates;
        out.rdbuf()->pubsetbuf(output_buffer.data(),output_buffer.size());
        out.open(output);
        if(!out) throw std::runtime_error("Cannot open output");
        if(!stats_path.empty()) {
            stats.open(stats_path);
            if(!stats) throw std::runtime_error("Cannot open stats file");
            stats<<"row,delay,wall_ms,settled,relaxations\n";
        }
        if(!trace_path.empty()) {
            trace.open(trace_path);
            if(!trace) throw std::runtime_error("Cannot open trace file");
            trace<<"row,delay,steps,hops,long_hops,turns,detour\n";
        }
        if(!certificate_path.empty()) {
            if(!certified_relative_error || cache_enabled || certificate_path==input || certificate_path==output || certificate_path==stats_path || certificate_path==trace_path)throw std::runtime_error("Certificates require certified mode, --no-cache, and distinct files");
            certificates.open(certificate_path);if(!certificates)throw std::runtime_error("Cannot open certificate file");certificates<<"row,lower,upper,settled,relaxations\n";
        }
        const auto cpu_start=std::clock();
        const bool fast=algorithm=="phase-certified" || algorithm=="approximate" || algorithm=="spatial" || algorithm=="port" || algorithm=="source-x" || algorithm=="target-x" || algorithm=="v2" || algorithm=="v3" || algorithm=="v3-forced" || algorithm=="v3-final" || algorithm=="v4-tree" || algorithm=="v4-table" || algorithm=="v4-horizontal" || algorithm=="v5-geometry" || algorithm=="v5-geometry-fused" || algorithm=="v6-pair" || algorithm=="v7-tree" || algorithm=="v9-tree" || algorithm=="v10-tree" || algorithm=="v14-tree" || algorithm=="v19-tree";
        if(!oracle_path.empty() && (!fast || oracle_path==input || oracle_path==output || oracle_path==stats_path))
            throw std::runtime_error("Path oracle requires an estimate algorithm and distinct files");
        std::unique_ptr<LocalPathOracle> local_oracle;
        if(!oracle_path.empty()) local_oracle=std::make_unique<LocalPathOracle>(oracle_path);
        if(!cycle_path.empty() && (!fast || cycle_path==input || cycle_path==output || cycle_path==stats_path))
            throw std::runtime_error("Cycle oracle requires an estimate algorithm and distinct files");
        if((algorithm=="v14-tree" || algorithm=="v19-tree") && (oracle_path.empty() || cycle_path.empty()))
            throw std::runtime_error("Tree route model requires --local-oracle and --cycle-oracle assets");
        std::unique_ptr<CyclePathOracle> cycle_oracle;
        if(!cycle_path.empty()) cycle_oracle=std::make_unique<CyclePathOracle>(cycle_path);
        if((!neural_path.empty() || !neural_second_path.empty() || macro_budget) && algorithm!="v19-tree") throw std::runtime_error("Neural/macro options require v19-tree");
        std::unique_ptr<PhaseRouteModel> neural;if(!neural_path.empty())neural=std::make_unique<PhaseRouteModel>(neural_path);
        if(!neural_second_path.empty() && (neural_path.empty() || !std::isfinite(neural_second_weight) || neural_second_weight<0 || neural_second_weight>1))throw std::runtime_error("Invalid neural ensemble");
        std::unique_ptr<PhaseRouteModel> neural_second;if(!neural_second_path.empty())neural_second=std::make_unique<PhaseRouteModel>(neural_second_path);
        if((exact_short_distance || exact_uncertainty) && (algorithm!="v19-tree" || !std::isfinite(exact_uncertainty) || exact_uncertainty<0 || exact_uncertainty>1 || (exact_uncertainty && !neural_second)))throw std::runtime_error("Invalid exact refinement options");
        if(certified_relative_error && ((algorithm!="v19-tree" && algorithm!="phase-certified") || !std::isfinite(certified_relative_error) || certified_relative_error<0 || certified_relative_error>.1))throw std::runtime_error("Invalid certified relative error");
        if(algorithm=="phase-certified" && (!certified_relative_error || phase_bounds_path.empty()))throw std::runtime_error("phase-certified requires --phase-bounds and --certified-relative-error");
        std::unique_ptr<PhaseLowerBound> phase_bounds;if(!phase_bounds_path.empty()) {if(!certified_relative_error)throw std::runtime_error("Phase bounds require certified mode");phase_bounds=std::make_unique<PhaseLowerBound>(phase_bounds_path);}
        std::unique_ptr<MacroPathOracle> macro;if(macro_budget)macro=std::make_unique<MacroPathOracle>(cycle_path,true);
        std::unique_ptr<PredictionCache> cache;
        if(cache_enabled && (algorithm=="v14-tree" || algorithm=="v19-tree")) cache=std::make_unique<PredictionCache>();
        FastPinParser parser;
        std::unique_ptr<Graph> graph;
        if(!fast || exact_short_distance || exact_uncertainty || certified_relative_error) graph=std::make_unique<Graph>();
        std::unique_ptr<Solver> solver;
        std::unique_ptr<CompactSolver> compact_solver;
        if(algorithm=="compressed" || exact_short_distance || exact_uncertainty || certified_relative_error) compact_solver=std::make_unique<CompactSolver>(*graph);
        else if(!fast) solver=std::make_unique<Solver>(*graph);
        out<<"From,To,delay\n";
        std::string line; uint64_t row=0;
        while(std::getline(in,line)) {
            auto record=trim_view(line);
            if(record.empty()) continue;
            auto comma=record.find(',');
            if(comma==record.npos || record.find(',',comma+1)!=record.npos) throw std::runtime_error("Invalid CSV row");
            std::string_view s=trim_view(record.substr(0,comma)),t=trim_view(record.substr(comma+1));
            const bool collect=stats.is_open();
            auto start=collect?std::chrono::steady_clock::now():std::chrono::steady_clock::time_point{};
            SearchStats counters;
            Node from=parser.pin(s),to=parser.pin(t);
            CompactSolver::Trace route;
            if(trace.is_open()) route=compact_solver->trace(from,to,counters);
            Distance d=INF;uint64_t cache_key=(uint64_t(from)<<32)|to;
            if(!cache || !cache->get(cache_key,d)) {
            Distance route_upper=INF;
            if(algorithm=="phase-certified" && cycle_oracle)route_upper=cycle_oracle->cap(from,to,route_upper,true);
            if(algorithm=="v14-tree" || algorithm=="v19-tree") {
                route_upper=std::min(route_upper,local_oracle->upper_bound(from,to));
                route_upper=cycle_oracle->cap(from,to,route_upper,algorithm=="v19-tree");
            }
            d=trace.is_open()?route.delay:
                algorithm=="phase-certified"?INF:
                algorithm=="approximate"?lookup_delay(from,to):
                algorithm=="spatial"?spatial_delay(from,to):
                algorithm=="port"?port_delay(from,to):
                algorithm=="source-x"?source_x_delay(from,to):
                algorithm=="target-x"?target_x_delay(from,to):
                algorithm=="v2"?v2_delay(from,to):
                algorithm=="v3"?v3_delay(from,to):
                algorithm=="v3-forced"?v3_forced_delay(from,to):
                algorithm=="v3-final"?v3_final_delay(from,to):
                algorithm=="v4-tree"?v4_tree_delay(from,to):
                algorithm=="v4-table"?v4_table_delay(from,to):
                algorithm=="v4-horizontal"?v4_horizontal_delay(from,to):
                algorithm=="v5-geometry"?v5_geometry_delay(from,to):
                algorithm=="v5-geometry-fused"?v5_geometry_fused_delay(from,to):
                algorithm=="v6-pair"?v6_pair_delay(from,to):
                algorithm=="v7-tree"?v7_tree_delay(from,to):
                algorithm=="v9-tree"?v9_tree_delay(from,to):
                algorithm=="v10-tree"?v10_tree_delay(from,to):
                algorithm=="v14-tree"?v14_tree_delay(from,to,route_upper):
                algorithm=="v19-tree"?v19_tree_delay(from,to,route_upper):
                compact_solver?(balanced_astar?compact_solver->solve_balanced(from,to,counters):exact_astar?compact_solver->solve_astar(from,to,counters):compact_solver->solve(from,to,counters)):solver->solve(from,to,algorithm=="bidirectional",counters);
            if(local_oracle && algorithm!="v14-tree" && algorithm!="v19-tree" && algorithm!="phase-certified") d=std::min(d,local_oracle->upper_bound(from,to));
            if(cycle_oracle && algorithm!="v14-tree" && algorithm!="v19-tree" && algorithm!="phase-certified") d=cycle_oracle->cap(from,to,d);
                bool exact_candidate=false,refined=false;
                if(neural) {
                    auto feature=topology_features(from,to);auto a=archdata::SITES[from/archdata::P],b=archdata::SITES[to/archdata::P];auto base=v6_pair_delay(from,to);
                    auto first=neural->predict(feature,a,b,base,route_upper,d);
                    if(neural_second) {auto second=neural_second->predict(feature,a,b,base,route_upper,d);exact_candidate=exact_uncertainty && 2*std::abs(double(first)-double(second))>exact_uncertainty*std::max(2.,double(first)+double(second));d=uint64_t(std::nearbyint((1-neural_second_weight)*double(first)+neural_second_weight*double(second)));}
                    else d=first;
                    d=std::min(route_upper,std::max(d,PhaseRouteModel::lower_bound(feature,a,b)));
                }
                auto xy1=archdata::SITES[from/archdata::P],xy2=archdata::SITES[to/archdata::P];
                if(exact_short_distance && unsigned(std::abs(xy1.x-xy2.x)+std::abs(xy1.y-xy2.y))<exact_short_distance) {d=compact_solver->solve_astar(from,to,counters,route_upper);counters.lower=counters.upper=d;refined=true;++exact_short_queries;}
                else if(exact_candidate) {d=compact_solver->solve_astar(from,to,counters,route_upper);counters.lower=counters.upper=d;refined=true;++exact_uncertain_queries;}
                if(macro && !refined) {route_upper=macro->cap(from,to,route_upper,macro_budget);d=std::min(d,route_upper);}
                if(certified_relative_error && !refined)d=phase_bounds?compact_solver->solve_phase(from,to,counters,*phase_bounds,route_upper,certified_relative_error,d):compact_solver->solve_balanced(from,to,counters,route_upper,certified_relative_error,d);
                if(cycle_extra_hops && cycle_oracle) d=cycle_oracle->cap(from,to,d,true);
                if(cache) cache->put(cache_key,d);
            }
            if(d>=INF) throw std::runtime_error("Unreachable query: "+std::string(s)+" -> "+std::string(t)+"; official output convention unspecified");
            out.write(s.data(),s.size());out.put(',');out.write(t.data(),t.size());out.put(',');
            char digits[32];auto end=std::to_chars(digits,digits+sizeof(digits),d);
            if(end.ec!=std::errc()) throw std::runtime_error("Cannot format delay");
            out.write(digits,end.ptr-digits);out.put('\n');
            ++row;
            if(progress && row%1000==0)std::cerr<<"progress="<<row<<" cpu="<<double(std::clock()-cpu_start)/CLOCKS_PER_SEC<<'\n';
            if(certificates.is_open())certificates<<row<<','<<counters.lower<<','<<counters.upper<<','<<counters.settled<<','<<counters.relaxations<<'\n';
            if(collect) {
                auto ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
                stats<<row<<','<<d<<','<<ms<<','<<counters.settled<<','<<counters.relaxations<<'\n';
                stats.flush();
            }
            if(trace.is_open()) {
                const auto& first=archdata::SITES[from/archdata::P];
                const auto& last=archdata::SITES[to/archdata::P];
                int x=first.x,y=first.y,steps=0,hops=0,long_hops=0,turns=0,axis=0,sign=0;
                auto segment=[&](int nx,int ny) {
                    int dx=nx-x,dy=ny-y,length=std::abs(dx)+std::abs(dy);
                    if(length) {
                        ++hops;steps+=length;long_hops+=length>1;
                        int next_axis=dx?1:2,next_sign=(dx?dx:dy)>0?1:-1;
                        if(axis && (axis!=next_axis || sign!=next_sign)) ++turns;
                        axis=next_axis;sign=next_sign;
                    }
                    x=nx;y=ny;
                };
                for(Node s:route.states) {
                    const auto& p=archdata::SITES[compact_solver->trace_site(s)];
                    segment(p.x,p.y);
                }
                segment(last.x,last.y);
                int direct=std::abs(last.x-first.x)+std::abs(last.y-first.y);
                trace<<row<<','<<d<<','<<steps<<','<<hops<<','<<long_hops<<','<<turns<<','<<steps-direct<<'\n';
            }
        }
        out.flush();
        if(certificates.is_open())certificates.flush();
        if(in.bad() || !out || (certificates.is_open() && !certificates) || (stats.is_open() && !stats) || (trace.is_open() && !trace)) throw std::runtime_error("File I/O failed");
        std::cerr<<"rows="<<row<<" cpu_seconds="<<double(std::clock()-cpu_start)/CLOCKS_PER_SEC<<" arch_sha256="<<archdata::HASH<<'\n';
        if(exact_short_distance || exact_uncertainty) std::cerr<<"exact_short_queries="<<exact_short_queries<<" exact_uncertain_queries="<<exact_uncertain_queries<<'\n';
        if(cache) std::cerr<<"cache_hits="<<cache->hits<<" cache_misses="<<cache->misses<<'\n';
        return 0;
    } catch(const std::exception& e) { std::cerr<<"error: "<<e.what()<<'\n'; return 1; }
}
