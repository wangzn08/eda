#pragma once
#include "routing_search.hpp"
#include <zlib.h>
#include "xz_decode.hpp"
#include <cstring>
#include "vertical_transient_model.hpp"
#include "horizontal_transient_model.hpp"
#include "joint_interaction_model.hpp"
#include "physical_portal_bank.hpp"
#include "transient_tail_patch.hpp"
#include "near_response_curve_model.hpp"
#include "prefix_dp_workspace.hpp"
#include "prefix_policy_model.hpp"
#include "ideal_action_policy.hpp"
#ifndef CORE_IDEAL_ACTION_POLICY
#define CORE_IDEAL_ACTION_POLICY 0
#endif
#ifndef CORE_PREFIX_POLICY
#define CORE_PREFIX_POLICY 0
#endif
#ifndef CORE_PHYSICAL_PREFIX_MEMO
#define CORE_PHYSICAL_PREFIX_MEMO 0
#endif
#ifndef CORE_CORRIDOR_ROW_CACHE
#define CORE_CORRIDOR_ROW_CACHE 0
#endif
#ifndef CORE_LEGAL_TERMINALS
#define CORE_LEGAL_TERMINALS 0
#endif
#ifndef CORE_LEGAL_FULL_MASK
#define CORE_LEGAL_FULL_MASK 0
#endif
#ifndef CORE_PREFIX_SUPERVISION
#define CORE_PREFIX_SUPERVISION 0
#endif
#ifndef CORE_NEAR_RESPONSE_CURVES
#define CORE_NEAR_RESPONSE_CURVES 0
#endif
#ifndef CORE_PHYSICAL_PREFIX
#define CORE_PHYSICAL_PREFIX 0
#endif
#ifndef CORE_HINT_PHASE_SCAN
#define CORE_HINT_PHASE_SCAN 0
#endif
#ifndef CORE_SPARSE_SOURCE_ITERATION
#define CORE_SPARSE_SOURCE_ITERATION 0
#endif
#ifndef CORE_SIMD_NEAR_HINTS
#define CORE_SIMD_NEAR_HINTS 0
#endif
#ifndef CORE_TAIL_SATURATION
#define CORE_TAIL_SATURATION 0
#endif
#ifndef CORE_TRANSIENT_TAIL
#define CORE_TRANSIENT_TAIL 0
#endif
#ifndef CORE_PHYSICAL_PORTALS
#define CORE_PHYSICAL_PORTALS 0
#endif
#include <memory>
#include <iostream>
#ifndef CORE_PREPARED_GEOMETRY
#define CORE_PREPARED_GEOMETRY 0
#endif
#ifndef CORE_ENDPOINT_RESEARCH
#define CORE_ENDPOINT_RESEARCH 0
#endif
#ifndef CORE_ROUTE_TRACE
#define CORE_ROUTE_TRACE 0
#endif
#ifndef CORE_PHASE_MAJOR
#define CORE_PHASE_MAJOR 0
#endif
#ifndef CORE_SHARED_CORRIDOR
#define CORE_SHARED_CORRIDOR 0
#endif
#ifndef CORE_CORE_PHASE_MAJOR
#define CORE_CORE_PHASE_MAJOR 0
#endif
#ifndef CORE_PACKED_NEAR
#define CORE_PACKED_NEAR 0
#endif
#ifndef CORE_PREFETCH_CELL
#define CORE_PREFETCH_CELL 0
#endif
#ifndef CORE_PREFETCH
#define CORE_PREFETCH 0
#endif
#ifndef CORE_DIRECT_NEAR
#define CORE_DIRECT_NEAR 0
#endif
#ifndef JOINT_CELL_ALIGN
#define JOINT_CELL_ALIGN 2
#endif
static_assert(JOINT_CELL_ALIGN==2 || JOINT_CELL_ALIGN==32,"Supported joint alignment");
// Exact finite-template storage; periodic extension remains approximate.
class CoreTemplateModel {
public:
    struct PrefixSupervision{uint16_t sx,sy,tx,ty,core,target;int32_t entry,base,expanded;};
    struct RouteTrace{int source_core=-1,target_core=-1,dx=0,dy=0,qx=0,qy=0,rx=0,ry=0,kind=0,entry_cost=0,source_x=0,source_y=0,margin=0,nominal_delay=0,terminal_cost=0,base0=0,base1=0,base2=0,base3=0,horizontal_delta=0,interaction_delta=0,cell_kind=0;};
struct BranchSummary{RouteTrace trace;Distance delay;};
struct NominalGeometry{Node site=0;int dx=0,dy=0,qx=0,qy=0,rx=0,ry=0;Distance gap=0;bool cross=false;};
    struct PreparedRequest {struct Branch{Node site;uint16_t port;uint16_t geometry;uint32_t cost;};Node source=0,target=0;uint32_t mask=UINT32_MAX;unsigned count=0;Distance local_best=INF;std::array<Branch,32>branches;std::array<NominalGeometry,32>geometry;unsigned geometry_count=0;};
private:
    static constexpr bool phase_major=CORE_PHASE_MAJOR;
    std::array<int,496>index;std::array<uint16_t,160>core_ports{};bool paired_terminal=false;unsigned corridor_all=0;
    std::vector<uint16_t>values;bool core_layout_ready=false;
    std::array<std::vector<std::pair<unsigned,unsigned>>,496>terminal;
    std::array<Distance,120>xgap{};
    std::array<Distance,550>ygap{};
    std::array<int,550>corridor_block{};
    bool envelope,has_far=false,corridor_geometry=false,interaction_enabled=false;
    unsigned shell_x=0,shell_y=0,growth_cap=UINT_MAX,far_period=4;
    std::unique_ptr<VerticalTransientModel>vertical;
    std::unique_ptr<HorizontalTransientModel>horizontal;
    std::unique_ptr<JointInteractionModel>interaction;
    std::unique_ptr<PhysicalPortalBank>physical_portals;
    std::unique_ptr<TransientTailPatch>tail_patch;
    std::unique_ptr<NearResponseCurveModel>near_response_curves;
    unsigned physical_blend=0;
    unsigned tail_growth_limit=UINT_MAX;
    unsigned prefix_depth=0,prefix_gate=0,prefix_beam=0,prefix_beam_margin=0;
    mutable PrefixDpWorkspace prefix_workspace;
    std::unique_ptr<PrefixPolicyModel>prefix_policy;unsigned prefix_policy_confidence=0;
    std::unique_ptr<IdealActionPolicy>ideal_action_policy;
    struct JointCell {int32_t base[4];int32_t slope_x,slope_y;};
    std::vector<JointCell>joint;
    struct alignas(JOINT_CELL_ALIGN) FarJointCell {uint16_t base[4];int16_t horizontal_delta,interaction_delta;int x_slope()const{return std::max(0,int(horizontal_delta));}int far_slope()const{return std::max(0,int(base[3])-int(base[2]));}};
    static_assert(sizeof(FarJointCell)==((12+JOINT_CELL_ALIGN-1)/JOINT_CELL_ALIGN)*JOINT_CELL_ALIGN,"Compact piecewise cell size");
    std::vector<FarJointCell>far_joint;
    struct ShortVerticalCell {uint16_t base[4];int far_slope()const{return std::max(0,int(base[3])-int(base[2]));}};
    static_assert(sizeof(ShortVerticalCell)==8,"Short vertical cell size");
    std::vector<ShortVerticalCell>short_vertical;
    struct HorizontalCell{uint16_t base;int16_t delta;};std::vector<int16_t>horizontal_cells;std::vector<HorizontalCell>target_horizontal_cells;std::array<int,496>horizontal_target_index{};unsigned horizontal_targets=0;
    HorizontalCell horizontal_cell(unsigned source,unsigned target,unsigned phase)const{HorizontalCell c;std::memcpy(&c,horizontal_cells.data()+((size_t(target)*1420+phase)*160+source)*2,4);return c;}
    std::vector<int>corridor_ports;
    std::array<int,496>hint_target{};unsigned hint_targets=0,hint_count=0,hint_width=0;
    std::vector<uint16_t>long_hints,vertical_hints;
    std::vector<uint8_t>long_hint_bytes,vertical_hint_bytes,near_hints,horizontal_hints;
    std::vector<uint16_t>near_values;

    struct SourceEntry{uint16_t vector,port;uint32_t cost;};std::array<std::vector<SourceEntry>,496>source_entries;
    std::array<int,496>source_hint_index{},source_hint_target{};unsigned source_hint_count=0,source_hint_targets=0;std::vector<uint32_t>source_masks;std::vector<uint8_t>source_submasks;unsigned source_adaptive_distance=0;
    template<class F>void each_source(unsigned port,uint32_t mask,F&&f)const{if(CORE_SPARSE_SOURCE_ITERATION && mask!=UINT32_MAX){while(mask){unsigned k=__builtin_ctz(mask);mask&=mask-1;f(source_entries[port][k]);}}else{unsigned k=0;for(auto e:source_entries[port]){if(mask==UINT32_MAX || (k<32 && (mask&(1u<<k))))f(e);++k;}}}
    size_t near_hint_offset(unsigned target,unsigned phase,unsigned source)const{return CORE_PACKED_NEAR && phase_major?(size_t(target)*4189+phase)*100+source*5/8:(size_t(target)*4189+phase)*160+source;}
    unsigned near_hint(unsigned target,unsigned phase,unsigned source)const{size_t pos=near_hint_offset(target,phase,source);if(CORE_PACKED_NEAR && phase_major){unsigned shift=(source*5)%8,value=near_hints[pos];if(shift>3)value|=unsigned(near_hints[pos+1])<<8;return (value>>shift)&31;}return near_hints[pos];}
    void store_near_hint(unsigned target,unsigned phase,unsigned source,unsigned value){size_t pos=near_hint_offset(target,phase,source);if(CORE_PACKED_NEAR && phase_major){if(value>=32)throw std::runtime_error("Packed near hint overflow");unsigned shift=(source*5)%8;near_hints[pos]|=uint8_t(value<<shift);if(shift>3)near_hints[pos+1]|=uint8_t(value>>(8-shift));}else near_hints[pos]=uint8_t(value);}
    size_t core_offset(unsigned source,unsigned target,unsigned phase)const{return CORE_CORE_PHASE_MAJOR && core_layout_ready?(size_t(target)*4189+phase)*160+source:(size_t(source)*160+target)*4189+phase;}
    Distance at(unsigned source,unsigned target,int x,int y)const{return values[core_offset(source,target,size_t(x+29)*71+y+35)];}
    void prefetch_nominal(int port,int target,int dx,int dy,bool cells=CORE_PREFETCH_CELL,const NominalGeometry*geometry=nullptr)const{
        if(!hint_count)return;
        int nx,ny,rx,ry;if(CORE_PREPARED_GEOMETRY && geometry){nx=geometry->qx;ny=geometry->qy;rx=geometry->rx;ry=geometry->ry;}else{int ax=std::abs(dx),ay=std::abs(dy);nx=ax>29?(ax-20)/10:0;ny=ay>35?(ay-24)/12:0;rx=(dx<0?-1:1)*(ax-nx*10);ry=(dy<0?-1:1)*(ay-ny*12);}unsigned source=index[port];
        if(nx && !ny && !target_horizontal_cells.empty() && horizontal_target_index[target]>=0){unsigned phase=((rx>0?10:0)+std::abs(rx)-20)*71+ry+35;__builtin_prefetch(target_horizontal_cells.data()+(size_t(horizontal_target_index[target])*1420+phase)*160+source);return;}
        if(hint_target[target]<0){if(index[target]<0)return;unsigned core=index[target];if(!nx && !ny)__builtin_prefetch(values.data()+core_offset(source,core,size_t(rx+29)*71+ry+35));else if(!nx && ny && !short_vertical.empty()){unsigned iy=(ry>0?12:0)+std::abs(ry)-24;__builtin_prefetch(short_vertical.data()+(size_t(core)*1416+size_t(rx+29)*24+iy)*160+source);}else if(nx && ny && !far_joint.empty()){unsigned ix=(rx>0?10:0)+std::abs(rx)-20,iy=(ry>0?12:0)+std::abs(ry)-24;__builtin_prefetch(far_joint.data()+(size_t(core)*480+ix*24+iy)*160+source);}else if(nx && !ny && !horizontal_cells.empty()){unsigned phase=((rx>0?10:0)+std::abs(rx)-20)*71+ry+35;__builtin_prefetch(horizontal_cells.data()+((size_t(core)*1420+phase)*160+source)*2);}return;}unsigned t=hint_target[target];
        if(!nx && !ny){if(!near_hints.empty()){unsigned phase=size_t(rx+29)*71+ry+35;size_t pos=near_hint_offset(t,phase,source);__builtin_prefetch(near_hints.data()+pos);if(cells){auto end=terminal[target][near_hint(t,phase,source)];__builtin_prefetch(values.data()+core_offset(source,end.first,size_t(rx+29)*71+ry+35));}}return;}
        unsigned yb=ny==1?0:ny<=6?1:2,iy=(ry>0?12:0)+std::abs(ry)-24;
        if(!nx && ny && !vertical_hint_bytes.empty()){size_t phase=size_t(rx+29)*24+iy,pos=((size_t(t)*3+yb)*1416+phase)*160+source;__builtin_prefetch(vertical_hint_bytes.data()+pos);if(cells){auto end=terminal[target][vertical_hint_bytes[pos]];__builtin_prefetch(short_vertical.data()+(size_t(end.first)*1416+phase)*160+source);}}
        else if(nx && !ny && !horizontal_hints.empty()){unsigned phase=((rx>0?10:0)+std::abs(rx)-20)*71+ry+35;size_t pos=(size_t(t)*1420+phase)*160+source;__builtin_prefetch(horizontal_hints.data()+pos);if(cells && !horizontal_cells.empty()){auto end=terminal[target][horizontal_hints[pos]];__builtin_prefetch(horizontal_cells.data()+((size_t(end.first)*1420+phase)*160+source)*2);}}
        else if(nx && ny && !long_hint_bytes.empty()){unsigned ix=(rx>0?10:0)+std::abs(rx)-20;size_t phase=ix*24+iy,pos=((size_t(t)*6+(nx==1?0:3)+yb)*480+phase)*160+source;__builtin_prefetch(long_hint_bytes.data()+pos);if(cells){auto end=terminal[target][long_hint_bytes[pos]];__builtin_prefetch(far_joint.data()+(size_t(end.first)*480+phase)*160+source);}}
    }
    Distance nominal(int port,int target,int dx,int dy,RouteTrace*trace=nullptr,const NominalGeometry*geometry=nullptr,uint32_t terminal_vectors=UINT32_MAX)const{
        auto allowed=[&](unsigned core){return !CORE_LEGAL_TERMINALS || terminal_vectors==UINT32_MAX || (terminal_vectors&(1u<<archdata::NETS[core].vector)) || (!dx&&!dy&&unsigned(index[port])==core);};
        if(CORE_NEAR_RESPONSE_CURVES && near_response_curves && NearResponseCurveModel::supports(dx,dy)){
            Distance best=INF;unsigned selected=0,cost=0;for(auto end:terminal[target]){if(!allowed(end.first))continue;int value=near_response_curves->cost(index[port],end.first,dx,dy);if(value<0)throw std::runtime_error("Negative nominal curve cost");Distance v=Distance(value)+end.second;if(v<best){best=v;selected=end.first;cost=end.second;}}
            if(CORE_ROUTE_TRACE && trace && best<INF){trace->source_core=index[port];trace->target_core=selected;trace->dx=dx;trace->dy=dy;trace->qx=0;trace->qy=(std::abs(dy)-24)/12;trace->rx=dx;trace->ry=(dy>0?1:-1)*(24+std::abs(dy)%12);trace->nominal_delay=int(best);trace->terminal_cost=cost;trace->cell_kind=4;}return best;
        }
        int qx,qy,x,y;if(CORE_PREPARED_GEOMETRY && geometry){qx=geometry->qx;qy=geometry->qy;x=geometry->rx;y=geometry->ry;}else{int ax=std::abs(dx),ay=std::abs(dy);qx=ax>29?(ax-20)/10:0;qy=ay>35?(ay-24)/12:0;if(qx)qx+=std::min(shell_x,unsigned((ax-qx*10)/10));if(qy)qy+=std::min(shell_y,unsigned((ay-qy*12)/12));x=(dx<0?-1:1)*(ax-qx*10);y=(dy<0?-1:1)*(ay-qy*12);}
        if(qx>0 && qy==0 && !target_horizontal_cells.empty() && horizontal_target_index[target]>=0 && (!CORE_LEGAL_TERMINALS||terminal_vectors==UINT32_MAX)){unsigned phase=((x>0?10:0)+std::abs(x)-20)*71+y+35;auto c=target_horizontal_cells[(size_t(horizontal_target_index[target])*1420+phase)*160+index[port]];int64_t v=c.base;if(qx>=2)v+=c.delta+int64_t(qx-2)*std::max(0,int(c.delta));return Distance(std::max<int64_t>(0,v))+Distance(qx)*125;}
        if(CORE_DIRECT_NEAR && (!CORE_LEGAL_TERMINALS||terminal_vectors==UINT32_MAX) && !near_values.empty() && qx==0 && qy==0 && hint_target[target]>=0)return near_values[(size_t(hint_target[target])*4189+size_t(x+29)*71+y+35)*160+index[port]];
        Distance best=INF;
        auto candidate=[&](int rx,int ry,int nx,int ny){
            Distance base=INF;unsigned selected_target=0,selected_cost=0;RouteTrace selected_metrics;
            const bool short_layout=!short_vertical.empty() && nx==0 && ny>0;
            const bool long_layout=(!joint.empty() || !far_joint.empty()) && nx>0 && ny>0;
            const unsigned ix=long_layout?unsigned((rx>0?10:0)+std::abs(rx)-20):0,iy=ny>0?unsigned((ry>0?12:0)+std::abs(ry)-24):0;
            const size_t source_pair=size_t(index[port])*160;
            const int interaction_weight=interaction_enabled && nx>0 && ny>0?int(std::min(std::min(unsigned(nx),5u)*6,std::min(unsigned(ny),6u)*5)):0;
            auto interpolate=[&](int difference){int v=difference*(ny-2);return far_period==6?v/4:v/2;};
            unsigned begin=0,limit=terminal[target].size();uint16_t hints=0;bool sparse=false;
            if(hint_count && hint_target[target]>=0 && (short_layout || long_layout || (!near_hints.empty() && nx==0 && ny==0))){
                unsigned ybucket=ny==1?0:ny<=6?1:2;size_t pair=size_t(index[port])*hint_targets+hint_target[target];
                if(nx==0 && ny==0){hints=phase_major?near_hint(hint_target[target],size_t(rx+29)*71+ry+35,index[port]):near_hints[pair*4189+size_t(rx+29)*71+ry+35];limit=1;}
                else{size_t position=short_layout?(phase_major?((size_t(hint_target[target])*3+ybucket)*1416+size_t(rx+29)*24+iy)*160+index[port]:(pair*3+ybucket)*1416+size_t(rx+29)*24+iy):(phase_major?((size_t(hint_target[target])*6+(nx==1?0:3)+ybucket)*480+ix*24+iy)*160+index[port]:(pair*6+(nx==1?0:3)+ybucket)*480+ix*24+iy);
                    hints=hint_width==1?(short_layout?vertical_hint_bytes[position]:long_hint_bytes[position]):(short_layout?vertical_hints[position]:long_hints[position]);limit=hint_count;
                }sparse=true;
            }
            if(hint_count && hint_target[target]>=0 && nx>0 && ny==0 && !horizontal_hints.empty()){size_t phase=size_t((rx>0?10:0)+std::abs(rx)-20)*71+ry+35;hints=horizontal_hints[(size_t(hint_target[target])*1420+phase)*160+index[port]];limit=1;sparse=true;}
            if(CORE_LEGAL_TERMINALS && sparse && terminal_vectors!=UINT32_MAX){bool invalid=false;for(unsigned rank=0;rank<limit;++rank)invalid|=!allowed(terminal[target][rank==0?hints&255:hints>>8].first);if(invalid){sparse=false;limit=terminal[target].size();}}
            for(unsigned rank=begin;rank<limit;++rank){auto end=terminal[target][sparse?(rank==0?hints&255:hints>>8):rank];if(!allowed(end.first))continue;int64_t value;RouteTrace metrics;
                if(short_layout){
                    const auto& cell=short_vertical[phase_major?(size_t(end.first)*1416+size_t(rx+29)*24+iy)*160+index[port]:((source_pair+end.first)*59+rx+29)*24+iy];
                    if(CORE_ROUTE_TRACE && trace){metrics.base0=cell.base[0];metrics.base1=cell.base[1];metrics.base2=cell.base[2];metrics.base3=cell.base[3];metrics.cell_kind=1;}if(ny==1)value=cell.base[0];else if(ny==2)value=cell.base[1];
                    else if(unsigned(ny)<far_period)value=int(cell.base[1])+interpolate(int(cell.base[2])-int(cell.base[1]));
                    else if(unsigned(ny)==far_period)value=cell.base[2];else value=cell.base[3]+int64_t((CORE_TAIL_SATURATION?std::min(unsigned(ny)-far_period-1,tail_growth_limit):unsigned(ny)-far_period-1))*cell.far_slope();
                    value+=end.second;
                }else if(long_layout){
                    size_t ji=(source_pair+end.first)*480+ix*24+iy;
                    if(!far_joint.empty()){
                        const auto& cell=far_joint[phase_major?(size_t(end.first)*480+ix*24+iy)*160+index[port]:ji];int64_t v;if(CORE_ROUTE_TRACE && trace){metrics.base0=cell.base[0];metrics.base1=cell.base[1];metrics.base2=cell.base[2];metrics.base3=cell.base[3];metrics.horizontal_delta=cell.horizontal_delta;metrics.interaction_delta=cell.interaction_delta;metrics.cell_kind=2;}
                        if(ny==1)v=cell.base[0];
                        else if(ny==2)v=cell.base[1];
                        else if(unsigned(ny)<far_period)v=int(cell.base[1])+interpolate(int(cell.base[2])-int(cell.base[1]));
                        else if(unsigned(ny)==far_period)v=cell.base[2];
                        else v=cell.base[3]+int64_t((CORE_TAIL_SATURATION?std::min(unsigned(ny)-far_period-1,tail_growth_limit):unsigned(ny)-far_period-1))*cell.far_slope();
                        if(nx>=2)v+=cell.horizontal_delta+int64_t(nx-2)*cell.x_slope();
                        if(interaction_enabled && !(CORE_MULTI_ANCHOR && interaction && interaction->multi()))v+=interaction_weight==30?int(cell.interaction_delta):int(cell.interaction_delta)*interaction_weight/30;
                        value=v+end.second;
                    }else{
                        const auto& cell=joint[ji];
                        value=cell.base[(nx>=2?2:0)+(ny>=2?1:0)]+int64_t(std::min(unsigned(std::max(0,nx-2)),growth_cap))*cell.slope_x+int64_t(std::min(unsigned(std::max(0,ny-2)),growth_cap))*cell.slope_y+end.second;
                    }
                }else if(nx>0 && ny==0 && !horizontal_cells.empty()){size_t phase=size_t((rx>0?10:0)+std::abs(rx)-20)*71+ry+35;auto c=horizontal_cell(index[port],end.first,phase);if(CORE_ROUTE_TRACE && trace){metrics.base0=c.base;metrics.base1=c.base+c.delta;metrics.base2=c.base;metrics.base3=c.base;metrics.horizontal_delta=c.delta;metrics.cell_kind=3;}value=int64_t(c.base)+end.second;if(nx>=2)value+=c.delta+int64_t(std::min(unsigned(nx-2),growth_cap))*std::max(0,int(c.delta));}else{value=int64_t(at(index[port],end.first,rx,ry))+end.second;if(vertical)value+=vertical->correction(index[port],end.first,rx,dy,growth_cap);if(horizontal)value+=horizontal->correction(index[port],end.first,ry,dx,growth_cap);}if(interaction && (far_joint.empty() || nx==0 || ny==0 || (CORE_MULTI_ANCHOR && interaction->multi())))value+=interaction->correction(index[port],end.first,rx,ry,dx,dy);if(CORE_TRANSIENT_TAIL && tail_patch && ny>6)value+=tail_patch->correction(index[port],end.first,rx,ry,ny);Distance v=Distance(std::max<int64_t>(0,value));if(v<base){base=v;selected_target=end.first;selected_cost=end.second;if(CORE_ROUTE_TRACE && trace){if(metrics.cell_kind==0)metrics.base0=metrics.base1=metrics.base2=metrics.base3=int(value)-int(end.second);selected_metrics=metrics;}}}
            Distance result=base+Distance(nx)*125+Distance(ny)*(dy>0?127:125);if(result<best){best=result;if(CORE_ROUTE_TRACE && trace){trace->source_core=index[port];trace->target_core=selected_target;trace->dx=dx;trace->dy=dy;trace->qx=nx;trace->qy=ny;trace->rx=rx;trace->ry=ry;trace->nominal_delay=int(result);trace->terminal_cost=selected_cost;trace->base0=selected_metrics.base0;trace->base1=selected_metrics.base1;trace->base2=selected_metrics.base2;trace->base3=selected_metrics.base3;trace->horizontal_delta=selected_metrics.horizontal_delta;trace->interaction_delta=selected_metrics.interaction_delta;trace->cell_kind=selected_metrics.cell_kind;}}
        };
        if(!envelope){candidate(x,y,qx,qy);return best;}
        // Compare all representatives in the same period class, for long displacements.
        int ax=std::abs(dx),ay=std::abs(dy);std::vector<std::pair<int,int>>xs,ys;
        if(ax<=29)xs.push_back({dx,0});
        else for(int rx=-29;rx<=29;++rx){int n=(dx<0?rx-dx:dx-rx);if(n>=0 && n%10==0)xs.push_back({rx,n/10});}
        if(ay<=35)ys.push_back({dy,0});
        else for(int ry=-35;ry<=35;++ry){int n=(dy<0?ry-dy:dy-ry);if(n>=0 && n%12==0)ys.push_back({ry,n/12});}
        for(auto a:xs)for(auto b:ys)candidate(a.first,b.first,a.second,b.second);
        return best;
    }
public:
    void enable_finite_hints(){if(envelope || shell_x || shell_y)throw std::runtime_error("Finite hints require original anchors");hint_target.fill(-1);hint_targets=0;for(unsigned t=0;t<496;++t)if(terminal[t].size()>1)hint_target[t]=hint_targets++;hint_count=hint_width=1;near_hints.assign(size_t(CORE_PACKED_NEAR && phase_major?100:160)*hint_targets*4189,0);for(unsigned source=0;source<160;++source)for(unsigned t=0;t<496;++t)if(hint_target[t]>=0)for(unsigned phase=0;phase<4189;++phase){Distance best=INF;unsigned selected=0;for(unsigned k=0;k<terminal[t].size();++k){auto e=terminal[t][k];Distance v=values[core_offset(source,e.first,phase)]+e.second;if(v<best){best=v;selected=k;}}if(phase_major)store_near_hint(hint_target[t],phase,source,selected);else near_hints[(size_t(source)*hint_targets+hint_target[t])*4189+phase]=selected;}}
    Distance finite_nominal(int port,int target,int dx,int dy)const{if(std::abs(dx)>29 || std::abs(dy)>35)return INF;return nominal(port,target,dx,dy);}
    void enable_all_corridors(unsigned mode){if(!CORE_ENDPOINT_RESEARCH)throw std::runtime_error("Endpoint research build required");if(mode<1 || mode>3 || corridor_ports.empty())throw std::runtime_error("All corridors require1..3 and prepared hubs");corridor_all=mode;}
    void enable_paired_terminal(){if(!CORE_ENDPOINT_RESEARCH)throw std::runtime_error("Endpoint research build required");if(hint_count!=1 || !phase_major || !target_horizontal_cells.empty())throw std::runtime_error("Paired terminal requires single stage hints");paired_terminal=true;}
    std::pair<unsigned,unsigned> selected_terminal(unsigned source,unsigned target,int dx,int dy)const{
        if(terminal[target].size()==1)return terminal[target][0];int ax=std::abs(dx),ay=std::abs(dy),nx=ax>29?(ax-20)/10:0,ny=ay>35?(ay-24)/12:0,rx=(dx<0?-1:1)*(ax-nx*10),ry=(dy<0?-1:1)*(ay-ny*12);unsigned t=hint_target[target],selected=0;
        if(!nx && !ny)selected=near_hint(t,size_t(rx+29)*71+ry+35,source);
        else if(nx && !ny){unsigned phase=((rx>0?10:0)+std::abs(rx)-20)*71+ry+35;selected=horizontal_hints[(size_t(t)*1420+phase)*160+source];}
        else{unsigned yb=ny==1?0:ny<=6?1:2,iy=(ry>0?12:0)+std::abs(ry)-24;if(!nx)selected=vertical_hint_bytes[((size_t(t)*3+yb)*1416+size_t(rx+29)*24+iy)*160+source];else{unsigned ix=(rx>0?10:0)+std::abs(rx)-20;selected=long_hint_bytes[((size_t(t)*6+(nx==1?0:3)+yb)*480+ix*24+iy)*160+source];}}
        return terminal[target][selected];
    }
    void prefetch_source_mask(Node from,Node to)const{
        unsigned port=from%496,target=to%496;if(!source_hint_count || source_hint_index[port]<0 || source_hint_target[target]<0)return;auto a=archdata::SITES[from/496],b=archdata::SITES[to/496];int dx=b.x-a.x,dy=b.y-a.y;if(std::abs(dy)<=35 || (std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89))return;unsigned xp=std::abs(dx)<=29?dx+29:59+(dx<0?10:0)+std::abs(dx)%10,phase=xp*24+(dy<0?12:0)+std::abs(dy)%12;__builtin_prefetch(source_masks.data()+(size_t(source_hint_index[port])*source_hint_targets+source_hint_target[target])*1896+phase);
    }
    void prepare_request(const Graph&graph,Node from,Node to,PreparedRequest&r)const{
        if(CORE_PREPARED_GEOMETRY && (envelope || shell_x || shell_y))throw std::runtime_error("Prepared geometry requires original anchor policy");r.source=from;r.target=to;r.count=0;r.geometry_count=0;r.mask=UINT32_MAX;r.local_best=INF;Node site=from/496;unsigned port=from%496,target=to%496;auto b=archdata::SITES[to/496];
        if(source_hint_count && source_hint_index[port]>=0){auto a=archdata::SITES[site];int dx=b.x-a.x,dy=b.y-a.y;bool cross=std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89;if(source_hint_target[target]>=0 && std::abs(dy)>35 && !cross){unsigned xp=std::abs(dx)<=29?dx+29:59+(dx<0?10:0)+std::abs(dx)%10,phase=xp*24+(dy<0?12:0)+std::abs(dy)%12;size_t pos=(size_t(source_hint_index[port])*source_hint_targets+source_hint_target[target])*1896+phase;r.mask=adaptive_mask(pos,source_masks[pos],dy);}}
        auto add=[&](Node site,unsigned port,Distance cost){if(r.count==r.branches.size())throw std::runtime_error("Prepared branch overflow");if(cost>UINT32_MAX)throw std::runtime_error("Prepared branch cost overflow");unsigned gi=0;if(CORE_PREPARED_GEOMETRY){for(;gi<r.geometry_count;++gi)if(r.geometry[gi].site==site)break;if(gi==r.geometry_count){auto a=archdata::SITES[site];auto&g=r.geometry[r.geometry_count++];g.site=site;g.dx=b.x-a.x;g.dy=b.y-a.y;int ax=std::abs(g.dx),ay=std::abs(g.dy);g.qx=ax>29?(ax-20)/10:0;g.qy=ay>35?(ay-24)/12:0;g.rx=(g.dx<0?-1:1)*(ax-g.qx*10);g.ry=(g.dy<0?-1:1)*(ay-g.qy*12);g.gap=Distance(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x])))+Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));g.cross=std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89;}}r.branches[r.count++]={site,uint16_t(port),uint16_t(gi),uint32_t(cost)};};
        if(site==to/496)for(auto e:graph.local_out(port))if(e.port==target)r.local_best=std::min(r.local_best,Distance(e.delay));
        if(index[port]>=0)add(site,port,0);else if(graph.net_out(port)>=0){auto net=archdata::NETS[graph.net_out(port)];auto m=graph.forward_vector_move(site,net.vector);if(m.site!=NONE)add(m.site,net.to,m.delay+net.delay);}else each_source(port,r.mask,[&](auto e){auto m=graph.forward_vector_move(site,e.vector);if(m.site!=NONE)add(m.site,e.port,Distance(e.cost)+m.delay);});
    }
    void prefetch_prepared(const PreparedRequest&r,bool cells)const{auto b=archdata::SITES[r.target/496];unsigned target=r.target%496;for(unsigned i=0;i<r.count;++i){auto branch=r.branches[i];if(CORE_PREPARED_GEOMETRY){const auto&g=r.geometry[branch.geometry];prefetch_nominal(branch.port,target,g.dx,g.dy,cells,&g);}else{auto a=archdata::SITES[branch.site];prefetch_nominal(branch.port,target,b.x-a.x,b.y-a.y,cells);}}}
    void prefetch_request(const Graph&graph,Node from,Node to,bool cells)const{
        if(!phase_major)return;Node site=from/496;unsigned port=from%496,target=to%496;auto b=archdata::SITES[to/496];uint32_t mask=UINT32_MAX;
        if(source_hint_count && source_hint_index[port]>=0){auto a=archdata::SITES[site];int dx=b.x-a.x,dy=b.y-a.y;bool cross=std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89;if(source_hint_target[target]>=0 && std::abs(dy)>35 && !cross){unsigned xp=std::abs(dx)<=29?dx+29:59+(dx<0?10:0)+std::abs(dx)%10,phase=xp*24+(dy<0?12:0)+std::abs(dy)%12;size_t pos=(size_t(source_hint_index[port])*source_hint_targets+source_hint_target[target])*1896+phase;mask=adaptive_mask(pos,source_masks[pos],dy);}}
        auto prepare=[&](Node s,unsigned p){auto a=archdata::SITES[s];prefetch_nominal(p,target,b.x-a.x,b.y-a.y,cells);};
        if(index[port]>=0)prepare(site,port);else if(graph.net_out(port)>=0){auto net=archdata::NETS[graph.net_out(port)];auto m=graph.forward_vector_move(site,net.vector);if(m.site!=NONE)prepare(m.site,net.to);}else each_source(port,mask,[&](auto e){auto m=graph.forward_vector_move(site,e.vector);if(m.site!=NONE)prepare(m.site,e.port);});
    }
    // Research-only nominal recurrence probe; excludes physical gaps and blocks.
    int64_t direct_nominal_probe(int source_port,int target_port,int dx,int dy)const{
        int ax=std::abs(dx),ay=std::abs(dy),qx=ax>29?(ax-20)/10:0,qy=ay>35?(ay-24)/12:0;
        int x=(dx<0?-1:1)*(ax-qx*10),y=(dy<0?-1:1)*(ay-qy*12);unsigned s=index[source_port],t=index[target_port];
        int64_t v=at(s,t,x,y)+qx*125+qy*(dy>0?127:125);if(vertical)v+=vertical->correction(s,t,x,dy,growth_cap);if(horizontal)v+=horizontal->correction(s,t,y,dx,growth_cap);return v;
    }
    Distance nominal_probe(int source_port,int target_port,int dx,int dy)const{return nominal(source_port,target_port,dx,dy);}
    void set_terminal_hint_count(unsigned count){if(count<1 || count>hint_width || (!hint_width))throw std::runtime_error("Invalid prepared hint count");hint_count=count;}
    void enable_terminal_hints(unsigned count,bool exact_near=false){
        if(count<1 || count>2 || far_joint.empty() || short_vertical.empty() || far_period!=6 || envelope)throw std::runtime_error("Terminal hints require complete distant6 layouts and1..2 candidates");
        hint_target.fill(-1);hint_targets=0;for(unsigned t=0;t<496;++t)if(terminal[t].size()>1){if(terminal[t].size()>255)throw std::runtime_error("Too many terminal candidates");hint_target[t]=hint_targets++;}
        // Every vertical correction is already fused for ny>0; ny==0 has zero correction.
        vertical.reset();
        hint_width=count;
        if(count==1){long_hint_bytes.resize(size_t(160)*hint_targets*6*480);vertical_hint_bytes.resize(size_t(160)*hint_targets*3*1416);}
        else{long_hints.resize(size_t(160)*hint_targets*6*480);vertical_hints.resize(size_t(160)*hint_targets*3*1416);}
        if(exact_near){if(CORE_DIRECT_NEAR)near_values.resize(size_t(160)*hint_targets*4189);else near_hints.assign(size_t(CORE_PACKED_NEAR && phase_major?100:160)*hint_targets*4189,0);}
        const int ys[3]={1,4,20};
        auto select=[](int64_t v,unsigned k,int64_t&b1,int64_t&b2,unsigned&i1,unsigned&i2){if(v<b1){b2=b1;i2=i1;b1=v;i1=k;}else if(v<b2){b2=v;i2=k;}};
        // Scan adjacent sources together for phase-major cells; preserve rank order/ties.
        if(CORE_HINT_PHASE_SCAN && phase_major){
            for(unsigned target=0;target<496;++target)if(hint_target[target]>=0){
                for(unsigned xb=0;xb<2;++xb)for(unsigned yb=0;yb<3;++yb){int nx=xb?6:1,ny=ys[yb],weight=std::min(std::min(nx,5)*6,std::min(ny,6)*5);
                    for(unsigned phase=0;phase<480;++phase){for(unsigned source=0;source<160;++source){size_t pair=size_t(source)*hint_targets+hint_target[target];int64_t b1=INT64_MAX,b2=INT64_MAX;unsigned i1=0,i2=0;
                        for(unsigned k=0;k<terminal[target].size();++k){auto end=terminal[target][k];const auto&c=far_joint[phase_major?(size_t(end.first)*480+phase)*160+source:(size_t(source)*160+end.first)*480+phase];int64_t v;
                            if(ny==1)v=c.base[0];else if(ny==2)v=c.base[1];else if(ny<6)v=int(c.base[1])+(int(c.base[2])-int(c.base[1]))*(ny-2)/4;else if(ny==6)v=c.base[2];else v=c.base[3]+int64_t(ny-7)*c.far_slope();
                            if(nx>=2)v+=c.horizontal_delta+int64_t(nx-2)*c.x_slope();
                            if(CORE_MULTI_ANCHOR && interaction && interaction->multi()){int rx=(phase/24<10?-1:1)*(20+(phase/24)%10),ry=(phase%24<12?-1:1)*(24+phase%12);v+=interaction->correction(source,end.first,rx,ry,rx+(rx<0?-1:1)*10*nx,ry+(ry<0?-1:1)*12*ny);}else if(interaction_enabled)v+=weight==30?int(c.interaction_delta):int(c.interaction_delta)*weight/30;
                            if(CORE_TRANSIENT_TAIL && tail_patch && ny>6){int rx=(phase/24<10?-1:1)*(20+(phase/24)%10),ry=(phase%24<12?-1:1)*(24+phase%12);v+=tail_patch->correction(source,end.first,rx,ry,ny);}v=std::max<int64_t>(0,v+end.second);select(v,k,b1,b2,i1,i2);
                        }size_t pos=phase_major?((size_t(hint_target[target])*6+xb*3+yb)*480+phase)*160+source:(pair*6+xb*3+yb)*480+phase;if(count==1)long_hint_bytes[pos]=uint8_t(i1);else long_hints[pos]=uint16_t(i1|(i2<<8));
                    }}
                }
                for(unsigned yb=0;yb<3;++yb){int ny=ys[yb];for(unsigned phase=0;phase<1416;++phase){for(unsigned source=0;source<160;++source){size_t pair=size_t(source)*hint_targets+hint_target[target];int64_t b1=INT64_MAX,b2=INT64_MAX;unsigned i1=0,i2=0;
                    for(unsigned k=0;k<terminal[target].size();++k){auto end=terminal[target][k];const auto&c=short_vertical[phase_major?(size_t(end.first)*1416+phase)*160+source:(size_t(source)*160+end.first)*1416+phase];int64_t v;
                        if(ny==1)v=c.base[0];else if(ny==2)v=c.base[1];else if(ny<6)v=int(c.base[1])+(int(c.base[2])-int(c.base[1]))*(ny-2)/4;else if(ny==6)v=c.base[2];else v=c.base[3]+int64_t(ny-7)*c.far_slope();
                        if(CORE_TRANSIENT_TAIL && tail_patch && ny>6){int rx=int(phase/24)-29,ry=(phase%24<12?-1:1)*(24+phase%12);v+=tail_patch->correction(source,end.first,rx,ry,ny);}select(v+end.second,k,b1,b2,i1,i2);
                    }size_t pos=phase_major?((size_t(hint_target[target])*3+yb)*1416+phase)*160+source:(pair*3+yb)*1416+phase;if(count==1)vertical_hint_bytes[pos]=uint8_t(i1);else vertical_hints[pos]=uint16_t(i1|(i2<<8));
                }}}
            }
            for(unsigned source=0;source<160;++source)for(unsigned target=0;target<496;++target)if(hint_target[target]>=0){size_t pair=size_t(source)*hint_targets+hint_target[target];
                if(exact_near){
                    const unsigned batch=CORE_SIMD_NEAR_HINTS && !core_layout_ready?8:1;
                    for(unsigned phase=0;phase<4189;phase+=batch){unsigned lanes=std::min(batch,4189-phase);uint32_t best[8];unsigned winner[8]{};std::fill(std::begin(best),std::end(best),UINT32_MAX);
                        for(unsigned k=0;k<terminal[target].size();++k){auto end=terminal[target][k];const uint16_t*row=values.data()+core_offset(source,end.first,phase);for(unsigned j=0;j<lanes;++j){uint32_t v=uint32_t(batch==8?row[j]:values[core_offset(source,end.first,phase+j)])+end.second;if(v<best[j]){best[j]=v;winner[j]=k;}}}
                        for(unsigned j=0;j<lanes;++j){unsigned ph=phase+j;if(CORE_DIRECT_NEAR){if(best[j]>65535)throw std::runtime_error("Near value overflow");near_values[(size_t(hint_target[target])*4189+ph)*160+source]=uint16_t(best[j]);}else if(phase_major)store_near_hint(hint_target[target],ph,source,winner[j]);else near_hints[pair*4189+ph]=uint8_t(winner[j]);}
                    }
                }
            }
        }else{
        for(unsigned source=0;source<160;++source){
            for(unsigned target=0;target<496;++target)if(hint_target[target]>=0){size_t pair=size_t(source)*hint_targets+hint_target[target];
                for(unsigned xb=0;xb<2;++xb)for(unsigned yb=0;yb<3;++yb){int nx=xb?6:1,ny=ys[yb],weight=std::min(std::min(nx,5)*6,std::min(ny,6)*5);
                    for(unsigned phase=0;phase<480;++phase){int64_t b1=INT64_MAX,b2=INT64_MAX;unsigned i1=0,i2=0;
                        for(unsigned k=0;k<terminal[target].size();++k){auto end=terminal[target][k];const auto&c=far_joint[phase_major?(size_t(end.first)*480+phase)*160+source:(size_t(source)*160+end.first)*480+phase];int64_t v;
                            if(ny==1)v=c.base[0];else if(ny==2)v=c.base[1];else if(ny<6)v=int(c.base[1])+(int(c.base[2])-int(c.base[1]))*(ny-2)/4;else if(ny==6)v=c.base[2];else v=c.base[3]+int64_t(ny-7)*c.far_slope();
                            if(nx>=2)v+=c.horizontal_delta+int64_t(nx-2)*c.x_slope();
                            if(CORE_MULTI_ANCHOR && interaction && interaction->multi()){int rx=(phase/24<10?-1:1)*(20+(phase/24)%10),ry=(phase%24<12?-1:1)*(24+phase%12);v+=interaction->correction(source,end.first,rx,ry,rx+(rx<0?-1:1)*10*nx,ry+(ry<0?-1:1)*12*ny);}else if(interaction_enabled)v+=weight==30?int(c.interaction_delta):int(c.interaction_delta)*weight/30;
                            if(CORE_TRANSIENT_TAIL && tail_patch && ny>6){int rx=(phase/24<10?-1:1)*(20+(phase/24)%10),ry=(phase%24<12?-1:1)*(24+phase%12);v+=tail_patch->correction(source,end.first,rx,ry,ny);}v=std::max<int64_t>(0,v+end.second);select(v,k,b1,b2,i1,i2);
                        }size_t pos=phase_major?((size_t(hint_target[target])*6+xb*3+yb)*480+phase)*160+source:(pair*6+xb*3+yb)*480+phase;if(count==1)long_hint_bytes[pos]=uint8_t(i1);else long_hints[pos]=uint16_t(i1|(i2<<8));
                    }
                }
                for(unsigned yb=0;yb<3;++yb){int ny=ys[yb];for(unsigned phase=0;phase<1416;++phase){int64_t b1=INT64_MAX,b2=INT64_MAX;unsigned i1=0,i2=0;
                    for(unsigned k=0;k<terminal[target].size();++k){auto end=terminal[target][k];const auto&c=short_vertical[phase_major?(size_t(end.first)*1416+phase)*160+source:(size_t(source)*160+end.first)*1416+phase];int64_t v;
                        if(ny==1)v=c.base[0];else if(ny==2)v=c.base[1];else if(ny<6)v=int(c.base[1])+(int(c.base[2])-int(c.base[1]))*(ny-2)/4;else if(ny==6)v=c.base[2];else v=c.base[3]+int64_t(ny-7)*c.far_slope();
                        if(CORE_TRANSIENT_TAIL && tail_patch && ny>6){int rx=int(phase/24)-29,ry=(phase%24<12?-1:1)*(24+phase%12);v+=tail_patch->correction(source,end.first,rx,ry,ny);}select(v+end.second,k,b1,b2,i1,i2);
                    }size_t pos=phase_major?((size_t(hint_target[target])*3+yb)*1416+phase)*160+source:(pair*3+yb)*1416+phase;if(count==1)vertical_hint_bytes[pos]=uint8_t(i1);else vertical_hints[pos]=uint16_t(i1|(i2<<8));
                }}
                if(exact_near){
                    const unsigned batch=CORE_SIMD_NEAR_HINTS && !core_layout_ready?8:1;
                    for(unsigned phase=0;phase<4189;phase+=batch){unsigned lanes=std::min(batch,4189-phase);uint32_t best[8];unsigned winner[8]{};std::fill(std::begin(best),std::end(best),UINT32_MAX);
                        for(unsigned k=0;k<terminal[target].size();++k){auto end=terminal[target][k];const uint16_t*row=values.data()+core_offset(source,end.first,phase);for(unsigned j=0;j<lanes;++j){uint32_t v=uint32_t(batch==8?row[j]:values[core_offset(source,end.first,phase+j)])+end.second;if(v<best[j]){best[j]=v;winner[j]=k;}}}
                        for(unsigned j=0;j<lanes;++j){unsigned ph=phase+j;if(CORE_DIRECT_NEAR){if(best[j]>65535)throw std::runtime_error("Near value overflow");near_values[(size_t(hint_target[target])*4189+ph)*160+source]=uint16_t(best[j]);}else if(phase_major)store_near_hint(hint_target[target],ph,source,winner[j]);else near_hints[pair*4189+ph]=uint8_t(winner[j]);}
                    }
                }

            }
            if(source%16==15)std::cerr<<"terminal_hint_source="<<source<<" complete\n";
        }        }
hint_count=count;if(!far_joint.empty() && !(CORE_MULTI_ANCHOR && interaction && interaction->multi()))interaction.reset();
    }
    static void load_hint_asset(const std::string&path,const char*magic,unsigned count,void*dest,size_t bytes){
        std::ifstream f(path,std::ios::binary);char m[8],hash[64];uint32_t stored_count;uint64_t stored_bytes;auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated hint asset");};read(m,8);read(hash,64);read(&stored_count,4);read(&stored_bytes,8);if(std::string(m,8)!=std::string(magic,8) || std::string(hash,64)!=archdata::HASH || stored_count!=count || stored_bytes!=bytes)throw std::runtime_error("Invalid hint asset header");std::vector<unsigned char>compressed((std::istreambuf_iterator<char>(f)),{});if(f.bad() || compressed.empty() || compressed.size()>100000000 || !decode_xz_exact(compressed.data(),compressed.size(),static_cast<unsigned char*>(dest),bytes))throw std::runtime_error("Invalid hint asset stream");
    }
    void save_hint_assets(const std::string&directory)const{
        auto save=[&](const char*name,const char*magic,unsigned count,const void*data,size_t bytes){std::ofstream f(directory+"/"+name,std::ios::binary);uint32_t c=count;uint64_t n=bytes;f.write(magic,8);f.write(archdata::HASH,64);f.write(reinterpret_cast<const char*>(&c),4);f.write(reinterpret_cast<const char*>(&n),8);f.write(static_cast<const char*>(data),bytes);if(!f)throw std::runtime_error("Hint export failed");};
        if(source_masks.empty() || horizontal_hints.empty())throw std::runtime_error("Export requires source and horizontal hints");save("source-hints.raw","SRCMSK01",source_hint_count,source_masks.data(),source_masks.size()*4);save("horizontal-hints.raw","HORHNT01",1,horizontal_hints.data(),horizontal_hints.size());
    }
    void enable_core_layout(){
        if(!CORE_CORE_PHASE_MAJOR || core_layout_ready)return;const size_t n=values.size();std::vector<uint8_t>visited((n+7)/8);auto destination=[](size_t i){size_t pair=i/4189,phase=i%4189;return ((pair%160)*4189+phase)*160+pair/160;};
        for(size_t i=0;i<n;++i)if(!(visited[i/8]&(1u<<(i%8)))){size_t current=i;uint16_t value=values[i];do{size_t next=destination(current);uint16_t displaced=values[next];values[next]=value;visited[current/8]|=1u<<(current%8);current=next;value=displaced;}while(current!=i);}core_layout_ready=true;
    }
    void enable_horizontal_layout(){
        if(!horizontal || !phase_major || far_joint.empty() || growth_cap!=UINT_MAX || envelope || shell_x || shell_y)throw std::runtime_error("Horizontal layout requires phase-major wide model");horizontal_cells=horizontal->take_values();horizontal.reset();
        for(unsigned source=0;source<160;++source)for(unsigned target=0;target<160;++target)for(unsigned y=0;y<71;++y)for(unsigned sign=0;sign<2;++sign){size_t start=((size_t(source)*160+target)*71+y)*40+sign*20;int16_t original[20];std::memcpy(original,horizontal_cells.data()+start,40);
            for(unsigned r=0;r<10;++r){int rx=(sign?1:-1)*(20+r),base=int(at(source,target,rx,int(y)-35))+original[r],delta=int(original[10+r])-original[r];if(base<0 || base>65535 || delta<-32768 || delta>32767)throw std::runtime_error("Horizontal fused overflow");uint16_t v=uint16_t(base);std::memcpy(horizontal_cells.data()+start+r,&v,2);horizontal_cells[start+10+r]=int16_t(delta);}
        }
        const size_t n=horizontal_cells.size();std::vector<uint8_t>visited((n+7)/8);auto destination=[](size_t i){unsigned r=i%10,band=(i/10)%2,sign=(i/20)%2,y=(i/40)%71;size_t pair=i/(40*71),source=pair/160,target=pair%160;return ((target*1420+(sign*10+r)*71+y)*160+source)*2+band;};
        for(size_t i=0;i<n;++i)if(!(visited[i/8]&(1u<<(i%8)))){size_t current=i;int16_t value=horizontal_cells[i];do{size_t next=destination(current);int16_t displaced=horizontal_cells[next];horizontal_cells[next]=value;visited[current/8]|=1u<<(current%8);current=next;value=displaced;}while(current!=i);}
    }
    void enable_target_horizontal_layout(){
        if(horizontal_cells.empty() || growth_cap!=UINT_MAX || envelope || shell_x || shell_y)throw std::runtime_error("Target horizontal layout requires unrestricted fused model");horizontal_target_index.fill(-1);horizontal_targets=0;for(unsigned t=0;t<496;++t)if(!terminal[t].empty())horizontal_target_index[t]=horizontal_targets++;
        target_horizontal_cells.resize(size_t(horizontal_targets)*1420*160);
        for(unsigned t=0;t<496;++t)if(horizontal_target_index[t]>=0)for(unsigned phase=0;phase<1420;++phase)for(unsigned source=0;source<160;++source){Distance best=INF;HorizontalCell winner{};for(auto end:terminal[t]){auto c=horizontal_cell(source,end.first,phase);int64_t value=int64_t(c.base)+c.delta+std::max(0,int(c.delta))+end.second;Distance score=Distance(std::max<int64_t>(0,value));if(score<best){best=score;unsigned base=unsigned(c.base)+end.second;if(base>65535)throw std::runtime_error("Target horizontal base overflow");winner={uint16_t(base),c.delta};}}target_horizontal_cells[(size_t(horizontal_target_index[t])*1420+phase)*160+source]=winner;}
        std::vector<int16_t>().swap(horizontal_cells);
    }
    void enable_horizontal_hints(const std::string&asset=""){
        if(!target_horizontal_cells.empty())return;

        if(!hint_count || (!horizontal && horizontal_cells.empty()) || !phase_major)throw std::runtime_error("Horizontal hints require phase-major prepared model");horizontal_hints.resize(size_t(hint_targets)*1420*160);if(!asset.empty()){load_hint_asset(asset,"HORHNT01",1,horizontal_hints.data(),horizontal_hints.size());for(unsigned t=0;t<496;++t)if(hint_target[t]>=0){size_t start=size_t(hint_target[t])*1420*160;for(size_t i=0;i<1420*160;++i)if(horizontal_hints[start+i]>=terminal[t].size())throw std::runtime_error("Invalid horizontal hint index");}return;}
        for(unsigned t=0;t<496;++t)if(hint_target[t]>=0)for(unsigned phase=0;phase<1420;++phase){int rx=(phase/71<10?-1:1)*(20+(phase/71)%10),ry=int(phase%71)-35,dx=(rx<0?-1:1)*(std::abs(rx)+30);for(unsigned source=0;source<160;++source){Distance best=INF;unsigned winner=0;
            for(unsigned k=0;k<terminal[t].size();++k){auto end=terminal[t][k];int64_t v;if(horizontal_cells.empty())v=int64_t(at(source,end.first,rx,ry))+horizontal->correction(source,end.first,ry,dx,growth_cap)+end.second;else{auto c=horizontal_cell(source,end.first,phase);v=int(c.base)+c.delta+std::max(0,int(c.delta))+end.second;}if(Distance(std::max<int64_t>(0,v))<best){best=Distance(std::max<int64_t>(0,v));winner=k;}}
            horizontal_hints[(size_t(hint_target[t])*1420+phase)*160+source]=uint8_t(winner);
        }}
    }
    void enable_adaptive_sources(unsigned distance){if(distance<36)throw std::runtime_error("Adaptive distance must be >=36");source_adaptive_distance=distance;}
    uint32_t adaptive_mask(size_t position,uint32_t mask,int dy)const{if(source_submasks.empty() || unsigned(std::abs(dy))<source_adaptive_distance)return mask;uint32_t selected=0;unsigned sub=source_submasks[position];for(unsigned i=0;mask;++i){unsigned bit=__builtin_ctz(mask);if(sub&(1u<<i))selected|=1u<<bit;mask&=mask-1;}return selected;}
    void enable_source_hints(const Graph&graph,unsigned count,const std::string&asset=""){
        if(count!=4 && count!=8 && count!=16)throw std::runtime_error("Source hints require8 or16");source_hint_index.fill(-1);unsigned sources=0;
        for(unsigned p=0;p<496;++p)if(index[p]<0 && graph.net_out(p)<0){unsigned n=0;for(auto e:graph.local_out(p))if(graph.net_out(e.port)>=0)++n;if(n>16){if(n>32)throw std::runtime_error("Source mask overflow");source_hint_index[p]=sources++;}}
        source_hint_target.fill(-1);source_hint_targets=0;for(unsigned t=0;t<496;++t)if(!terminal[t].empty())source_hint_target[t]=source_hint_targets++;source_masks.resize(size_t(sources)*source_hint_targets*1896);source_hint_count=count;if(source_adaptive_distance){if(count!=8 || !asset.empty())throw std::runtime_error("Adaptive sources require generated8 candidate hints");source_submasks.resize(source_masks.size());}if(!asset.empty()){load_hint_asset(asset,"SRCMSK01",count,source_masks.data(),source_masks.size()*4);for(unsigned p=0;p<496;++p)if(source_hint_index[p]>=0){size_t start=size_t(source_hint_index[p])*source_hint_targets*1896;for(size_t i=0;i<size_t(source_hint_targets)*1896;++i)if(__builtin_popcount(source_masks[start+i])!=int(count) || (source_entries[p].size()<32 && (source_masks[start+i]>>source_entries[p].size())))throw std::runtime_error("Invalid source hint mask");}return;}
        for(unsigned p=0;p<496;++p)if(source_hint_index[p]>=0){for(unsigned target=0;target<496;++target)if(source_hint_target[target]>=0)for(unsigned phase=0;phase<1896;++phase){unsigned xp=phase/24;int dx=xp<59?int(xp)-29:(xp>=69?-1:1)*(40+(xp-59)%10),dy=((phase/12)%2?-1:1)*(264+phase%12);std::vector<std::pair<Distance,unsigned>>ranks;unsigned i=0;
            for(auto e:graph.local_out(p)){int ni=graph.net_out(e.port);if(ni>=0){auto net=archdata::NETS[ni];auto v=archdata::VECTORS[net.vector];Distance cost=nominal(net.to,target,dx-v.x,dy-v.y)+e.delay+net.delay;ranks.push_back({cost,i++});}}
            std::sort(ranks.begin(),ranks.end());uint32_t mask=0;for(unsigned k=0;k<std::min(count,unsigned(ranks.size()));++k)mask|=1u<<ranks[k].second;size_t pos=(size_t(source_hint_index[p])*source_hint_targets+source_hint_target[target])*1896+phase;source_masks[pos]=mask;if(source_adaptive_distance){uint32_t top4=0;for(unsigned k=0;k<std::min(4u,unsigned(ranks.size()));++k)top4|=1u<<ranks[k].second;unsigned sub=0,rank=0;for(unsigned bit=0;bit<32;++bit)if(mask&(1u<<bit)){if(top4&(1u<<bit))sub|=1u<<rank;++rank;}source_submasks[pos]=uint8_t(sub);}
        }std::cerr<<"source_hint_port="<<p<<" complete\n";}
    }
    void set_tail_growth_limit(unsigned limit){tail_growth_limit=limit;}
    void enable_transient_tail(const std::string&path){if(!CORE_TRANSIENT_TAIL)throw std::runtime_error("Tail research disabled");tail_patch=std::make_unique<TransientTailPatch>(path);}
    void enable_near_response_curves(const std::string&path,bool derive_far=false){if(!CORE_NEAR_RESPONSE_CURVES)throw std::runtime_error("Curve research disabled");near_response_curves=std::make_unique<NearResponseCurveModel>(path);if(derive_far){if(!vertical||!far_joint.empty()||!short_vertical.empty())throw std::runtime_error("Curve far derivation requires original vertical layout");vertical->rebuild_far_delta([&](unsigned s,unsigned t,int x,int dy){int sign=dy>0?1:-1,ny=(std::abs(dy)-24)/12,y=sign*(24+std::abs(dy)%12);return near_response_curves->cost(s,t,x,dy)-int(at(s,t,x,y))-ny*(dy>0?127:125);});far_period=6;has_far=true;}}
    void enable_joint_interaction(const std::string&path){if(!has_far||far_period!=6||!horizontal||!far_joint.empty()||!joint.empty())throw std::runtime_error("Interaction requires original distant6 layout");interaction=std::make_unique<JointInteractionModel>(path,core_ports);interaction_enabled=true;}
    void set_physical_prefix(unsigned depth,unsigned gate){if(!CORE_PHYSICAL_PREFIX||depth>8||gate>2||(CORE_ROUTE_TRACE&&depth))throw std::runtime_error("Physical prefix research configuration; trace export unsupported");prefix_depth=depth;prefix_gate=gate;}
    void set_physical_prefix_beam(unsigned width){if(!CORE_PHYSICAL_PREFIX||width>32)throw std::runtime_error("Physical prefix beam width");prefix_beam=width;}
    void set_physical_prefix_beam_margin(unsigned margin){prefix_beam_margin=margin;}
    void enable_prefix_policy(const std::string&path){if(!CORE_PREFIX_POLICY||!CORE_PHYSICAL_PREFIX)throw std::runtime_error("Prefix policy research build required");prefix_policy=std::make_unique<PrefixPolicyModel>(path);}
    void set_prefix_policy_confidence(unsigned threshold){if(threshold>255)throw std::runtime_error("Policy confidence");prefix_policy_confidence=threshold;}
    void enable_ideal_action_policy(const std::string&path){if(!CORE_IDEAL_ACTION_POLICY||!CORE_PHYSICAL_PREFIX||hint_count!=1||!phase_major)throw std::runtime_error("Ideal action policy research configuration");ideal_action_policy=std::make_unique<IdealActionPolicy>(path);}
    void set_physical_blend(unsigned blend){if(blend>4)throw std::runtime_error("Portal blend");physical_blend=blend;}
    void enable_physical_portals(const std::string&path){if(!CORE_PHYSICAL_PORTALS)throw std::runtime_error("Physical portal research disabled");physical_portals=std::make_unique<PhysicalPortalBank>(path);}
    void enable_corridor_hubs(unsigned count){
        if(!corridor_geometry || !count || count>32)throw std::runtime_error("Corridor hubs require geometry and1..32 hubs");
        corridor_ports.clear();std::vector<std::pair<unsigned,int>>ports;
        for(auto net:archdata::NETS){auto v=archdata::VECTORS[net.vector];if(std::abs(v.x)+std::abs(v.y)>=10)ports.push_back({net.delay,net.to});}
        std::sort(ports.begin(),ports.end());for(auto p:ports)if(std::find(corridor_ports.begin(),corridor_ports.end(),p.second)==corridor_ports.end()){corridor_ports.push_back(p.second);if(corridor_ports.size()==count)break;}
    }
    void enable_short_vertical_layout(){
        if(!has_far || far_joint.empty())throw std::runtime_error("Wide joint layout requires far joint layout");
        short_vertical.resize(size_t(160)*160*59*24);
        for(unsigned s=0;s<160;++s)for(unsigned t=0;t<160;++t)for(int x=-29;x<=29;++x)for(unsigned iy=0;iy<24;++iy){
            int sy=iy<12?-1:1,r=iy%12,y=sy*(24+r);auto& cell=short_vertical[phase_major?(size_t(t)*1416+size_t(x+29)*24+iy)*160+s:((size_t(s)*160+t)*59+x+29)*24+iy];
            unsigned bands[4]={36,48,24+12*far_period,36+12*far_period};int v[4];
            for(unsigned b=0;b<4;++b){v[b]=vertical->correction(s,t,x,sy*(bands[b]+r),growth_cap);int base=int(at(s,t,x,y))+v[b];if(base<0 || base>65535)throw std::runtime_error("Short joint base overflow");cell.base[b]=uint16_t(base);}
            int slope=std::max(0,v[3]-v[2]);if(slope>65535)throw std::runtime_error("Short joint slope overflow");
        }
    }
    void enable_joint_layout(){
        if(!vertical || !horizontal || envelope || shell_x || shell_y)throw std::runtime_error("Joint layout requires both original-anchor transients");
        if(has_far)far_joint.resize(size_t(160)*160*480);else joint.resize(size_t(160)*160*480);
        for(unsigned source=0;source<160;++source)for(unsigned target=0;target<160;++target)for(unsigned ix=0;ix<20;++ix)for(unsigned iy=0;iy<24;++iy){
            int sx=ix<10?-1:1,sy=iy<12?-1:1,x=sx*(20+ix%10),y=sy*(24+iy%12);
            int32_t h[2]={horizontal->correction(source,target,y,sx*(30+ix%10),growth_cap),horizontal->correction(source,target,y,sx*(40+ix%10),growth_cap)};
            int32_t v[2]={vertical->correction(source,target,x,sy*(36+iy%12),growth_cap),vertical->correction(source,target,x,sy*(48+iy%12),growth_cap)};
            size_t ji=(size_t(source)*160+target)*480+ix*24+iy;
            if(has_far){
                auto& fc=far_joint[phase_major?(size_t(target)*480+ix*24+iy)*160+source:ji];
                int32_t vf[2]={vertical->correction(source,target,x,sy*(24+12*int(far_period)+int(iy%12)),growth_cap),vertical->correction(source,target,x,sy*(36+12*int(far_period)+int(iy%12)),growth_cap)};
                int32_t bases[4]={int32_t(at(source,target,x,y))+h[0]+v[0],int32_t(at(source,target,x,y))+h[0]+v[1],int32_t(at(source,target,x,y))+h[0]+vf[0],int32_t(at(source,target,x,y))+h[0]+vf[1]};
                for(unsigned b=0;b<4;++b){if(bases[b]<0 || bases[b]>65535)throw std::runtime_error("Compact joint base overflow");fc.base[b]=uint16_t(bases[b]);}
                int delta=h[1]-h[0];if(delta < -32768 || delta>32767)throw std::runtime_error("Compact joint delta overflow");fc.horizontal_delta=int16_t(delta);
                auto slope=[](int d){if(d>65535)throw std::runtime_error("Compact joint slope overflow");return uint16_t(std::max(0,d));};
                fc.interaction_delta=interaction?int16_t(interaction->raw_delta(source,target,x,y)):0;
                slope(delta);slope(v[1]-v[0]);slope(vf[1]-vf[0]);
            }else{
                auto& cell=joint[ji];
                for(unsigned a=0;a<2;++a)for(unsigned b=0;b<2;++b)cell.base[a*2+b]=int32_t(at(source,target,x,y))+h[a]+v[b];
                cell.slope_x=std::max(0,h[1]-h[0]);cell.slope_y=std::max(0,v[1]-v[0]);
            }
        }
    }
    std::pair<float,float>gap_features(Node source,Node target)const{
        auto a=archdata::SITES[source/496],b=archdata::SITES[target/496];
        return {float(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x]))),float(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])))};
    }
    explicit CoreTemplateModel(const std::string&path,bool use_envelope=false,unsigned sx=0,unsigned sy=0,const std::string&transient_path="",unsigned cap=UINT_MAX,const std::string&horizontal_path="",const std::string&far_path="",bool use_corridor=false,const std::string&interaction_path=""):envelope(use_envelope),corridor_geometry(use_corridor),shell_x(sx),shell_y(sy),growth_cap(cap){
        if(sx>2 || sy>2 || (use_envelope && (sx || sy)))throw std::runtime_error("Invalid template shell policy");
        std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated core template");};
        char magic[8],hash[64];std::array<uint16_t,160>ports;uint64_t decoded;
        read(magic,8);read(hash,64);read(ports.data(),320);read(&decoded,8);
        if((std::string(magic,8)!="COREZL01" && std::string(magic,8)!="COREXZ01") || std::string(hash,64)!=archdata::HASH || decoded!=214476800)throw std::runtime_error("Invalid core template header");
        index.fill(-1);for(unsigned i=0;i<160;++i){if(ports[i]>=496 || index[ports[i]]>=0)throw std::runtime_error("Invalid core ports");index[ports[i]]=i;core_ports[i]=ports[i];terminal[ports[i]].push_back({i,0});}
        if(!transient_path.empty()){if(sx || sy || use_envelope)throw std::runtime_error("Transient requires original anchor policy");vertical=std::make_unique<VerticalTransientModel>(transient_path,ports);}
        if(!horizontal_path.empty()){if(sx || sy || use_envelope)throw std::runtime_error("Horizontal transient requires original anchors");horizontal=std::make_unique<HorizontalTransientModel>(horizontal_path,ports);}
        if(!far_path.empty()){if(!vertical || cap!=UINT_MAX)throw std::runtime_error("Far delta requires vertical transient and unlimited growth cap");vertical->load_far_delta(far_path,ports);far_period=vertical->first_far_period();has_far=true;}
        if(!interaction_path.empty()){if(!has_far || far_period!=6 || !horizontal)throw std::runtime_error("Interaction requires distant6 and horizontal baseline");interaction=std::make_unique<JointInteractionModel>(interaction_path,ports);interaction_enabled=true;}
        for(auto arc:archdata::ARCS)if(index[arc.from]>=0)terminal[arc.to].push_back({unsigned(index[arc.from]),unsigned(arc.delay)});
        std::array<int,496>net_by_port;net_by_port.fill(-1);for(unsigned i=0;i<std::size(archdata::NETS);++i)net_by_port[archdata::NETS[i].from]=i;for(auto arc:archdata::ARCS)if(net_by_port[arc.to]>=0){auto n=archdata::NETS[net_by_port[arc.to]];source_entries[arc.from].push_back({uint16_t(n.vector),uint16_t(n.to),uint32_t(arc.delay+n.delay)});}
        std::vector<unsigned char>compressed((std::istreambuf_iterator<char>(f)),{});
        if(f.bad() || compressed.empty() || compressed.size()>100000000)throw std::runtime_error("Invalid core payload size");
        values.resize(decoded/2);if(std::string(magic,8)=="COREXZ01"){if(!decode_xz_exact(compressed.data(),compressed.size(),reinterpret_cast<unsigned char*>(values.data()),decoded))throw std::runtime_error("Invalid core XZ stream");}else{z_stream stream{};stream.next_in=compressed.data();stream.avail_in=unsigned(compressed.size());stream.next_out=reinterpret_cast<Bytef*>(values.data());stream.avail_out=unsigned(decoded);
        if(inflateInit(&stream)!=Z_OK)throw std::runtime_error("Core inflate initialization failed");
        int result=inflate(&stream,Z_FINISH);bool valid=result==Z_STREAM_END && stream.total_out==decoded && stream.avail_in==0;inflateEnd(&stream);
        if(!valid)throw std::runtime_error("Invalid core compressed stream");}
        for(size_t pair=0;pair<160*160;++pair)for(int x=0;x<59;++x)for(int y=0;y<71;++y){size_t i=pair*4189+x*71+y;int16_t delta;std::memcpy(&delta,&values[i],2);int value=delta;if(x)value+=values[i-71];if(y)value+=values[i-1];if(x && y)value-=values[i-72];if(value<0 || value>65535)throw std::runtime_error("Core inverse transform overflow");values[i]=uint16_t(value);}
        corridor_block.fill(-1);for(unsigned i=0;i<std::size(archdata::BLOCKS);++i){auto block=archdata::BLOCKS[i];if(block.left==76 && block.right==89)for(int y=block.lower;y<=block.upper;++y){if(corridor_block[y]>=0)throw std::runtime_error("Overlapping corridor bands");corridor_block[y]=i;}}
        for(auto l:archdata::LINES){if(l.vertical)for(int x=l.site+1;x<120;++x)xgap[x]+=l.delay;else for(int y=l.site+1;y<550;++y)ygap[y]+=l.delay;}
    }
    void validate_periodic_specialization()const{
        if(!phase_major||hint_count!=1||hint_width!=1||far_period!=6||envelope||shell_x||shell_y||core_layout_ready||far_joint.empty()||short_vertical.empty()||horizontal_cells.empty()||near_hints.empty()||!interaction_enabled||!source_hint_count||CORE_MULTI_ANCHOR||CORE_TRANSIENT_TAIL||CORE_TAIL_SATURATION||CORE_DIRECT_NEAR||corridor_ports.size()!=1||CORE_CORRIDOR_ROW_CACHE||!CORE_SHARED_CORRIDOR)throw std::runtime_error("Unsupported periodic specialization state");
    }
    // One hinted terminal and fixed packed layouts, specialized from nominal().
    // This method preserves V158's finite values, interpolation, truncation,
    // and tie policy; it does not claim exact physical shortest paths.
    Distance periodic_nominal(int port,int target,const NominalGeometry&g)const{
        unsigned source=index[port],nx=g.qx,ny=g.qy;int rx=g.rx,ry=g.ry;unsigned selected=0;
        if(terminal[target].size()>1){unsigned t=hint_target[target];
            if(!nx&&!ny)selected=near_hint(t,size_t(rx+29)*71+ry+35,source);
            else if(nx&&!ny){unsigned phase=((rx>0?10:0)+std::abs(rx)-20)*71+ry+35;selected=horizontal_hints[(size_t(t)*1420+phase)*160+source];}
            else{unsigned yb=ny==1?0:ny<=6?1:2,iy=(ry>0?12:0)+std::abs(ry)-24;if(!nx)selected=vertical_hint_bytes[((size_t(t)*3+yb)*1416+size_t(rx+29)*24+iy)*160+source];else{unsigned ix=(rx>0?10:0)+std::abs(rx)-20;selected=long_hint_bytes[((size_t(t)*6+(nx==1?0:3)+yb)*480+ix*24+iy)*160+source];}}
        }
        auto end=terminal[target][selected];int64_t value;
        if(ny){unsigned iy=(ry>0?12:0)+std::abs(ry)-24;
            if(!nx){const auto&c=short_vertical[(size_t(end.first)*1416+size_t(rx+29)*24+iy)*160+source];value=ny==1?c.base[0]:ny==2?c.base[1]:ny<6?int(c.base[1])+(int(c.base[2])-int(c.base[1]))*int(ny-2)/4:ny==6?c.base[2]:c.base[3]+int64_t(ny-7)*c.far_slope();}
            else{unsigned ix=(rx>0?10:0)+std::abs(rx)-20;const auto&c=far_joint[(size_t(end.first)*480+ix*24+iy)*160+source];value=ny==1?c.base[0]:ny==2?c.base[1]:ny<6?int(c.base[1])+(int(c.base[2])-int(c.base[1]))*int(ny-2)/4:ny==6?c.base[2]:c.base[3]+int64_t(ny-7)*c.far_slope();if(nx>=2)value+=c.horizontal_delta+int64_t(nx-2)*c.x_slope();int weight=std::min(std::min(nx,5u)*6,std::min(ny,6u)*5);value+=weight==30?int(c.interaction_delta):int(c.interaction_delta)*weight/30;}
        }else if(nx){unsigned phase=((rx>0?10:0)+std::abs(rx)-20)*71+ry+35;auto c=horizontal_cell(source,end.first,phase);value=c.base;if(nx>=2)value+=c.delta+int64_t(nx-2)*std::max(0,int(c.delta));}
        else value=at(source,end.first,rx,ry);
        value+=end.second;return Distance(std::max<int64_t>(0,value))+Distance(nx)*125+Distance(ny)*(g.dy>0?127:125);
    }
    // Fixed-profile evaluation for ordinary paths and the single-hub corridor.
    // The two shared target-side corridor slots follow the original order.
    // Research callbacks and inactive layouts stay outside this hot path.
    Distance predict_periodic_prepared(const Graph&graph,const PreparedRequest&r)const{
        if constexpr(!(CORE_PREPARED_GEOMETRY && !CORE_ROUTE_TRACE && !CORE_ENDPOINT_RESEARCH && !CORE_LEGAL_TERMINALS && !CORE_PHYSICAL_PREFIX))return predict(graph,r.source,r.target,nullptr,&r);
        if(r.source==r.target)return 0;
        auto geometry=[](int dx,int dy){NominalGeometry g;g.dx=dx;g.dy=dy;int ax=std::abs(dx),ay=std::abs(dy);g.qx=ax>29?(ax-20)/10:0;g.qy=ay>35?(ay-24)/12:0;g.rx=(dx<0?-1:1)*(ax-g.qx*10);g.ry=(dy<0?-1:1)*(ay-g.qy*12);return g;};
        Distance best=r.local_best;int target=r.target%496;auto b=archdata::SITES[r.target/496];std::array<Distance,2>second{};std::array<bool,2>ready{};
        for(unsigned i=0;i<r.count;++i){const auto&branch=r.branches[i];const auto&g=r.geometry[branch.geometry];Distance value;
            if(!g.cross)value=periodic_nominal(branch.port,target,g);
            else{
                auto a=archdata::SITES[branch.site];const archdata::Block*block=nullptr;if(corridor_block[a.y]>=0){auto&c=archdata::BLOCKS[corridor_block[a.y]];if(b.y>=c.lower&&b.y<=c.upper)block=&c;}
                value=block?INF:periodic_nominal(branch.port,target,g);
                if(block){
                    auto corridor=[&](int cy,unsigned slot){int hub=corridor_ports[0];Distance first=periodic_nominal(branch.port,hub,geometry(82-a.x,cy-a.y));if(!ready[slot]){second[slot]=periodic_nominal(hub,target,geometry(b.x-82,b.y-cy));ready[slot]=true;}
                        Distance detour=Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[cy])))+Distance(std::llabs(int64_t(ygap[b.y])-int64_t(ygap[cy])))-Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));return first+second[slot]+detour;};
                    if(block->lower>0)value=corridor(block->lower-1,0);
                    if(block->upper+1<archdata::HEIGHT)value=std::min(value,corridor(block->upper+1,1));
                }
                value=std::min(value,periodic_nominal(branch.port,target,geometry(g.dx+(g.dx>0?-14:14),g.dy))+292);
            }
            best=std::min(best,Distance(branch.cost)+value+g.gap);
        }
        return best<INF?best:predict(graph,r.source,r.target,nullptr,&r);
    }
    Distance predict(const Graph&graph,Node source,Node target,RouteTrace*trace=nullptr,const PreparedRequest*prepared=nullptr,bool allow_paired=true,std::vector<BranchSummary>*branch_records=nullptr,std::vector<PrefixSupervision>*supervision=nullptr,std::vector<uint16_t>*policy_actions=nullptr)const{
        if(source==target)return 0;Node site=source/496;int port=source%496,tp=target%496;auto b=archdata::SITES[target/496];Distance best=INF;
        uint32_t mask=prepared?prepared->mask:UINT32_MAX;if(!prepared && source_hint_count && source_hint_index[port]>=0){auto a=archdata::SITES[site];int dx=b.x-a.x,dy=b.y-a.y;bool cross=std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89;if(source_hint_target[tp]>=0 && std::abs(dy)>35 && !cross){unsigned xp=std::abs(dx)<=29?dx+29:59+(dx<0?10:0)+std::abs(dx)%10,phase=xp*24+(dy<0?12:0)+std::abs(dy)%12;size_t pos=(size_t(source_hint_index[port])*source_hint_targets+source_hint_target[tp])*1896+phase;mask=adaptive_mask(pos,source_masks[pos],dy);}}
        std::array<int,8>portal_rows{};std::array<Distance,8>portal_costs;unsigned portal_count=0;Distance runner_up=INF;RouteTrace candidate_trace;std::array<Distance,64>shared_second;std::array<bool,64>shared_ready{};std::array<int,64>shared_rows{};
        auto arrival_mask=[&](Node s){uint32_t m=graph.reverse_vector_mask(s);return CORE_LEGAL_FULL_MASK && m==(UINT32_MAX>>(32-archdata::K))?UINT32_MAX:m;};
        const auto final_b=b;const int final_tp=tp;const uint32_t final_terminal_vectors=CORE_LEGAL_TERMINALS?arrival_mask(target/496):UINT32_MAX;
        auto bound=[&](Node s,int p){auto a=archdata::SITES[s],b=final_b;int tp=final_tp;uint32_t terminal_vectors=final_terminal_vectors;Distance last_cost=0;if(CORE_ENDPOINT_RESEARCH && paired_terminal && allow_paired){auto end=selected_terminal(index[p],tp,b.x-a.x,b.y-a.y);int ni=graph.net_in(core_ports[end.first]);if(ni<0)throw std::runtime_error("Paired terminal input lacks Net");auto m=graph.net_move(target/496,ni,true);if(m.site==NONE)return INF;b=archdata::SITES[m.site];tp=archdata::NETS[ni].from;if(CORE_LEGAL_TERMINALS)terminal_vectors=arrival_mask(m.site);last_cost=Distance(end.second)+m.delay+archdata::NETS[ni].delay;}int dx=b.x-a.x,dy=b.y-a.y;bool cross=std::min(a.x,b.x)<76 && std::max(a.x,b.x)>89;
            const archdata::Block*block=nullptr;if(corridor_geometry && cross && corridor_block[a.y]>=0){auto&candidate=archdata::BLOCKS[corridor_block[a.y]];if(b.y>=candidate.lower && b.y<=candidate.upper)block=&candidate;}
            Distance physical_value=INF;Distance value=block?INF:nominal(p,tp,dx,dy,CORE_ROUTE_TRACE && trace?&candidate_trace:nullptr,nullptr,terminal_vectors);if(CORE_ROUTE_TRACE && trace)candidate_trace.kind=cross?1:0;
            if(CORE_ENDPOINT_RESEARCH && corridor_all && cross && !block){
                auto open_row=[&](int y,int toward){int bi=corridor_block[y];if(bi<0)return y;auto z=archdata::BLOCKS[bi];int cy=toward<y?z.lower-1:z.upper+1;if(cy<0)cy=z.upper+1;if(cy>=550)cy=z.lower-1;return cy;};
                auto through=[&](int cy){Distance result=INF;for(int hub:corridor_ports){Distance second=INF;bool cached=false;if(corridor_ports.size()==1 && !(CORE_ENDPOINT_RESEARCH && paired_terminal)){for(unsigned k=0;k<portal_count;++k)if(portal_rows[k]==cy){second=portal_costs[k];cached=true;break;}}if(!cached){second=nominal(hub,tp,b.x-82,b.y-cy,nullptr,nullptr,terminal_vectors);if(corridor_ports.size()==1 && !(CORE_ENDPOINT_RESEARCH && paired_terminal) && portal_count<portal_rows.size()){portal_rows[portal_count]=cy;portal_costs[portal_count++]=second;}}result=std::min(result,nominal(p,hub,82-a.x,cy-a.y)+second);}Distance extra=Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[cy])))+Distance(std::llabs(int64_t(ygap[b.y])-int64_t(ygap[cy])))-Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));return result+extra;};
                int tc=open_row(b.y,a.y),sc=open_row(a.y,b.y);value=corridor_all==2?through(sc):through(tc);if(corridor_all==3 && sc!=tc)value=std::min(value,through(sc));
            }
            if(cross){
                if(block){
                    auto corridor=[&](int cy,bool lower){
                        if(corridor_ports.empty()){int extra=lower?std::min(a.y,b.y)-block->lower+1:block->upper-std::max(a.y,b.y)+1;return nominal(p,tp,dx,(lower?-1:1)*(std::abs(dy)+2*extra),nullptr,nullptr,terminal_vectors);}
                        Distance best=INF;int cx=82;
                        unsigned h=0;for(int hub:corridor_ports){RouteTrace second_trace;Distance first=nominal(p,hub,cx-a.x,cy-a.y),second;unsigned slot=h*2+(lower?0:1);if(CORE_SHARED_CORRIDOR && !(CORE_ENDPOINT_RESEARCH && paired_terminal) && !(CORE_ROUTE_TRACE && trace)){if(!shared_ready[slot] || (CORE_CORRIDOR_ROW_CACHE && shared_rows[slot]!=cy)){shared_second[slot]=nominal(hub,tp,b.x-cx,b.y-cy,nullptr,nullptr,terminal_vectors);shared_ready[slot]=true;shared_rows[slot]=cy;}second=shared_second[slot];}else second=nominal(hub,tp,b.x-cx,b.y-cy,CORE_ROUTE_TRACE && trace?&second_trace:nullptr,nullptr,terminal_vectors);if(first+second<best){best=first+second;if(CORE_ROUTE_TRACE && trace){candidate_trace=second_trace;candidate_trace.source_core=index[p];candidate_trace.kind=lower?3:4;candidate_trace.nominal_delay=int(best);}}++h;}
                        Distance detour=Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[cy])))+Distance(std::llabs(int64_t(ygap[b.y])-int64_t(ygap[cy])))-Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));
                        return best+detour;
                    };
                    RouteTrace lower_trace;if(block->lower>0){value=corridor(block->lower-1,true);if(CORE_ROUTE_TRACE && trace)lower_trace=candidate_trace;}
                    if(block->upper+1<archdata::HEIGHT){Distance upper=corridor(block->upper+1,false);if(upper<value)value=upper;else if(CORE_ROUTE_TRACE && trace)candidate_trace=lower_trace;}
                }
                if(CORE_PHYSICAL_PORTALS && physical_portals){auto physical=physical_portals->cost(index[p],tp,a.x,a.y,b.x,b.y);if(physical<INF){auto gap=Distance(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x])))+Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));if(physical<gap)throw std::runtime_error("Physical portal gap underflow");physical_value=value=physical-gap;if(CORE_ROUTE_TRACE && trace){candidate_trace.kind=5;candidate_trace.nominal_delay=int(value);}}}
                RouteTrace alternate;Distance crossed=nominal(p,tp,dx+(dx>0?-14:14),dy,CORE_ROUTE_TRACE && trace?&alternate:nullptr,nullptr,terminal_vectors)+292;if(CORE_PHYSICAL_PORTALS && physical_value<INF && physical_blend){value=Distance(std::nearbyint((double(4-physical_blend)*std::min(value,crossed)+double(physical_blend)*physical_value)/4));}else if(crossed<value){value=crossed;if(CORE_ROUTE_TRACE && trace){candidate_trace=alternate;candidate_trace.kind=2;}}
            }return value+last_cost+Distance(std::llabs(int64_t(xgap[a.x])-int64_t(xgap[b.x])))+Distance(std::llabs(int64_t(ygap[a.y])-int64_t(ygap[b.y])));};
        if(CORE_PREFETCH && phase_major){auto prepare=[&](int ni){auto m=graph.net_move(site,ni,false);if(m.site!=NONE){auto a=archdata::SITES[m.site];prefetch_nominal(archdata::NETS[ni].to,tp,b.x-a.x,b.y-a.y);}};if(index[port]>=0){auto a=archdata::SITES[site];prefetch_nominal(port,tp,b.x-a.x,b.y-a.y);}else if(graph.net_out(port)>=0)prepare(graph.net_out(port));else each_source(port,mask,[&](auto e){auto m=graph.forward_vector_move(site,e.vector);if(m.site!=NONE){auto a=archdata::SITES[m.site];prefetch_nominal(e.port,tp,b.x-a.x,b.y-a.y);}});}
        if(prepared)best=prepared->local_best;else if(site==target/496)for(auto e:graph.local_out(port))if(e.port==tp)best=std::min(best,Distance(e.delay));
        if(CORE_PHYSICAL_PREFIX_MEMO && prefix_depth)prefix_workspace.begin();
        auto extend=[&](auto&&self,Node s,int p,unsigned depth)->Distance{
            uint64_t key=((uint64_t(s)*496+unsigned(p))<<4)|depth;Distance value;uint16_t best_action=65535;
            if(CORE_PHYSICAL_PREFIX_MEMO && prefix_workspace.get(key,value))return value;
            if(!depth)value=bound(s,p);else{value=INF;
                if(s==target/496){if(p==tp)value=0;for(auto e:graph.local_out(p))if(e.port==tp)value=std::min(value,Distance(e.delay));}
                bool policy_used=false;
                if((CORE_PREFIX_POLICY && prefix_policy)||(CORE_IDEAL_ACTION_POLICY && ideal_action_policy)){auto a=archdata::SITES[s];PrefixPolicyModel::Actions actions;if(CORE_IDEAL_ACTION_POLICY && ideal_action_policy){auto end=selected_terminal(index[p],tp,b.x-a.x,b.y-a.y);unsigned net=ideal_action_policy->select(index[p],end.first,b.x-a.x,b.y-a.y);if(net<160){actions.first=archdata::NETS[net].from;actions.second=actions.first;actions.confidence=255;}}else actions=prefix_policy->select(index[p],tp,a.x,a.y,b.x,b.y);unsigned count=actions.confidence<prefix_policy_confidence?2:1;for(unsigned k=0;k<count;++k){unsigned action=k?actions.second:actions.first;if(action>=496 || (k && action==actions.first))continue;int ni=graph.net_out(action);if(ni<0)continue;auto m=graph.net_move(s,ni,false);if(m.site==NONE)continue;for(auto e:graph.local_out(p))if(e.port==action){policy_used=true;Distance rest=self(self,m.site,archdata::NETS[ni].to,depth-1);if(rest<INF){Distance v=Distance(e.delay)+archdata::NETS[ni].delay+m.delay+rest;if(v<value){value=v;best_action=e.port;}}}}}
                if(!policy_used || value>=INF){if(prefix_beam && depth>1){
                    // Heuristic shortlist only; the nominal estimate is not an
                    // admissible lower bound, so this is an accuracy experiment.
                    struct Candidate{Node site;int port;Distance cost,rank;uint16_t action;};
                    std::array<Candidate,32> selected;unsigned used=0;
                    for(auto e:graph.local_out(p)){int ni=graph.net_out(e.port);if(ni<0)continue;auto m=graph.net_move(s,ni,false);if(m.site==NONE)continue;int next=archdata::NETS[ni].to;Distance cost=Distance(e.delay)+archdata::NETS[ni].delay+m.delay,rank=cost+self(self,m.site,next,0);unsigned pos=used;while(pos && selected[pos-1].rank>rank)--pos;if(pos>=prefix_beam)continue;unsigned end=std::min(used,prefix_beam-1);for(unsigned j=end;j>pos;--j)selected[j]=selected[j-1];selected[pos]={m.site,next,cost,rank,uint16_t(e.port)};used=std::min(used+1,prefix_beam);}
                    for(unsigned i=0;i<used;++i){auto c=selected[i];if(i && prefix_beam_margin && c.rank>selected[0].rank+prefix_beam_margin)break;Distance rest=self(self,c.site,c.port,depth-1);if(rest<INF && c.cost+rest<value){value=c.cost+rest;best_action=c.action;}}
                }else for(auto e:graph.local_out(p)){int ni=graph.net_out(e.port);if(ni<0)continue;auto m=graph.net_move(s,ni,false);if(m.site==NONE)continue;Distance rest=self(self,m.site,archdata::NETS[ni].to,depth-1);if(rest<INF){Distance v=Distance(e.delay)+archdata::NETS[ni].delay+m.delay+rest;if(v<value){value=v;best_action=e.port;}}}}}
            if(CORE_PHYSICAL_PREFIX_MEMO)prefix_workspace.put(key,value,best_action);return value;
        };
        auto consider=[&](Node s,int p,Distance cost){bool expand=CORE_PHYSICAL_PREFIX&&prefix_depth;if(expand&&prefix_gate){auto a=archdata::SITES[s];if(prefix_gate==1)expand=a.x<16||a.x>103||a.y<16||a.y>533||(a.x>=60&&a.x<=105&&a.y%100<=65);else{expand=false;for(auto l:archdata::LINES)if(std::abs((l.vertical?a.x:a.y)-l.site)<=16){expand=true;break;}}}Distance rest=expand?extend(extend,s,p,prefix_depth):bound(s,p),v=cost+rest;if(CORE_PREFIX_SUPERVISION && supervision && rest<INF){auto a=archdata::SITES[s];Distance base=extend(extend,s,p,0);if(base<INF){supervision->push_back({uint16_t(a.x),uint16_t(a.y),uint16_t(b.x),uint16_t(b.y),uint16_t(index[p]),uint16_t(tp),int32_t(cost),int32_t(base),int32_t(rest)});if(policy_actions)policy_actions->push_back(prefix_workspace.action(((uint64_t(s)*496+unsigned(p))<<4)|prefix_depth));}}if(CORE_ROUTE_TRACE && branch_records){auto t=candidate_trace;auto a=archdata::SITES[s];t.source_x=a.x;t.source_y=a.y;t.entry_cost=int(cost);branch_records->push_back({t,v});}if(v<best){if(CORE_ROUTE_TRACE && trace)runner_up=best;best=v;if(CORE_ROUTE_TRACE && trace){*trace=candidate_trace;auto a=archdata::SITES[s];trace->source_x=a.x;trace->source_y=a.y;trace->entry_cost=int(cost);}}else if(CORE_ROUTE_TRACE && trace)runner_up=std::min(runner_up,v);};
        auto after_net=[&](int ni,Distance cost){auto m=graph.net_move(site,ni,false);if(m.site!=NONE)consider(m.site,archdata::NETS[ni].to,cost+m.delay+archdata::NETS[ni].delay);};
        auto after_entry=[&](const SourceEntry&e){auto m=graph.forward_vector_move(site,e.vector);if(m.site!=NONE)consider(m.site,e.port,Distance(e.cost)+m.delay);};
        if(prepared){for(unsigned i=0;i<prepared->count;++i){auto branch=prepared->branches[i];if(CORE_PREPARED_GEOMETRY && !CORE_ROUTE_TRACE && !CORE_ENDPOINT_RESEARCH && !(CORE_PHYSICAL_PREFIX&&prefix_depth)){const auto&g=prepared->geometry[branch.geometry];if(!g.cross){best=std::min(best,Distance(branch.cost)+nominal(branch.port,tp,g.dx,g.dy,nullptr,&g,final_terminal_vectors)+g.gap);continue;}}consider(branch.site,branch.port,branch.cost);}}else if(index[port]>=0)consider(site,port,0);else if(graph.net_out(port)>=0)after_net(graph.net_out(port),0);else each_source(port,mask,[&](auto e){after_entry(e);});
        if(mask!=UINT32_MAX && best>=INF)for(auto e:source_entries[port])after_entry(e);
        if(best>=INF && CORE_ENDPOINT_RESEARCH && paired_terminal && allow_paired)return predict(graph,source,target,trace,prepared,false);if(CORE_ROUTE_TRACE && trace)trace->margin=runner_up>=INF?65535:int(runner_up-best);return best;
    }
};
