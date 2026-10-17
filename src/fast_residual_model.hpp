#pragma once
#include "routing_search.hpp"
#include <memory>
#include "fast_architecture_features.hpp"
class FastResidualModel {
 struct Split{uint16_t feature,border;};struct Tree{std::vector<Split>split;std::vector<double>leaf;};
 std::vector<Tree>trees;static constexpr int features=123;std::array<std::vector<float>,features>borders;std::vector<unsigned>active_features;std::array<std::vector<uint16_t>,features>integer_bins;double scale=1,bias=0;
 std::unique_ptr<FastArchitectureFeatures>feature_builder;
 bool obstacle_phase=false,boundary_features=false,asymmetric=false;
 struct AsymNode{uint16_t feature,left=0,right=0;double number;};std::vector<std::vector<AsymNode>>asym_trees;
 struct PrefixQuantizer{std::array<std::vector<float>,features>border;std::array<std::vector<uint16_t>,features>rank;};
 std::array<std::unique_ptr<PrefixQuantizer>,4>prefix_quantizer;
 std::array<float,features> expand(const std::array<float,71>& original,Node source,Node target)const{
  std::array<float,features> x{};std::copy(original.begin(),original.end(),x.begin());
  if(boundary_features){unsigned i=71;for(Node node:{source,target}){auto site=archdata::SITES[node/496];int cx=site.x,cy=site.y,phase=cy%100;
   const int values[]={cx,119-cx,cy,549-cy,std::abs(cx-75),std::abs(cx-90),phase,49-phase,99-phase,int(phase<50)};for(int v:values)x[i++]=v;
   for(int step:{2,4,8,16}){x[i++]=std::min(cx,step);x[i++]=std::min(119-cx,step);x[i++]=std::min(cy,step);x[i++]=std::min(549-cy,step);}
  }}
  if(asymmetric){unsigned i=71;auto a=archdata::SITES[source/496],b=archdata::SITES[target/496];int dx=b.x-a.x,dy=b.y-a.y;int rx=(dx%10+10)%10,ry=(dy%12+12)%12;
   for(Node node:{source,target}){auto site=archdata::SITES[node/496];int cx=site.x,cy=site.y,p=node%496,phase=cy%100;
    const int values[]={cx,119-cx,cy,549-cy,std::abs(cx-75),std::abs(cx-90),phase,49-phase,99-phase,p,p*120+rx*12+ry,p*100+phase,p*12+std::min(std::abs(dx)/10,11),p*46+std::min(std::abs(dy)/12,45)};for(int v:values)x[i++]=v;
   }
  }return x;
 }
 double value(const std::array<float,features>&x,unsigned count=UINT_MAX)const{
  if(asymmetric){double result=0;for(unsigned t=0;t<std::min<size_t>(count,asym_trees.size());++t){const auto&tree=asym_trees[t];unsigned n=0;while(tree[n].feature!=65535){const auto&v=tree[n];n=double(x[v.feature])<=v.number?v.left:v.right;}result+=tree[n].number;}return result;}
  const PrefixQuantizer*q=count==64?prefix_quantizer[0].get():count==128?prefix_quantizer[1].get():count==256?prefix_quantizer[2].get():count==512?prefix_quantizer[3].get():nullptr;
  std::array<uint16_t,features>bin;for(unsigned i:active_features){if(!q && !integer_bins[i].empty() && x[i]>=-1024 && x[i]<=8192 && x[i]==float(int(x[i]))){bin[i]=integer_bins[i][int(x[i])+1024];}else if(q){auto position=std::lower_bound(q->border[i].begin(),q->border[i].end(),x[i])-q->border[i].begin();bin[i]=q->rank[i][position];}else bin[i]=std::lower_bound(borders[i].begin(),borders[i].end(),x[i])-borders[i].begin();}double result=0;
  const unsigned limit=std::min<size_t>(count,trees.size());
  for(unsigned i=0;i<limit;++i){const auto&t=trees[i];unsigned leaf=0;if(t.split.size()==10){auto bit=[&](unsigned k){return unsigned(bin[t.split[k].feature]>t.split[k].border)<<k;};leaf=bit(0)|bit(1)|bit(2)|bit(3)|bit(4)|bit(5)|bit(6)|bit(7)|bit(8)|bit(9);}else for(size_t k=0;k<t.split.size();++k)leaf|=unsigned(bin[t.split[k].feature]>t.split[k].border)<<k;result+=t.leaf[leaf];}
  return scale*result+bias;
 }
public:
 void enable_integer_bins(){
  for(unsigned i:active_features)if(i!=22){auto& table=integer_bins[i];table.resize(9217);for(int value=-1024;value<=8192;++value)table[value+1024]=uint16_t(std::lower_bound(borders[i].begin(),borders[i].end(),float(value))-borders[i].begin());}
 }
 explicit FastResidualModel(const std::string&path,unsigned count){
  std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated residual model");};char magic[8];uint32_t total;read(magic,8);read(&total,4);
  if(std::string(magic,8)=="ASYBND01"){
   asymmetric=true;obstacle_phase=true;if(!count || count>total || total>4096)throw std::runtime_error("Invalid asymmetric tree count");
   for(unsigned t=0;t<count;++t){uint16_t n;read(&n,2);if(!n || n>=4096)throw std::runtime_error("Invalid asymmetric nodes");std::vector<AsymNode>tree(n);
    for(unsigned i=0;i<n;++i){auto&v=tree[i];read(&v.feature,2);if(v.feature!=65535){read(&v.left,2);read(&v.right,2);if(v.feature>=99 || v.left<=i || v.right<=i || v.left>=n || v.right>=n)throw std::runtime_error("Invalid asymmetric split");}read(&v.number,8);if(!std::isfinite(v.number))throw std::runtime_error("Invalid asymmetric number");}asym_trees.push_back(std::move(tree));
   }feature_builder=std::make_unique<FastArchitectureFeatures>(true);return;
  }
  read(&scale,8);read(&bias,8);boundary_features=std::string(magic,8)=="FASTBND1";obstacle_phase=std::string(magic,8)=="FASTOBS1" || boundary_features;if((std::string(magic,8)!="FASTRES1" && !obstacle_phase) || !count || count>total || total>4096)throw std::runtime_error("Invalid residual model");
  struct Raw{std::vector<std::pair<uint32_t,float>>split;std::vector<double>leaf;};std::vector<Raw>raw(count);
  for(auto&t:raw){uint32_t depth;read(&depth,4);if(depth>12)throw std::runtime_error("Invalid residual depth");for(unsigned i=0;i<depth;++i){uint32_t feature;float border;read(&feature,4);read(&border,4);if(feature>=features || !std::isfinite(border))throw std::runtime_error("Invalid residual split");t.split.push_back({feature,border});borders[feature].push_back(border);}t.leaf.resize(1u<<depth);read(t.leaf.data(),t.leaf.size()*8);}
  bool needs_topology=false;for(int i=29;i<71;++i)needs_topology|=!borders[i].empty();feature_builder=std::make_unique<FastArchitectureFeatures>(needs_topology);
  for(auto&b:borders){std::sort(b.begin(),b.end());b.erase(std::unique(b.begin(),b.end()),b.end());}
  for(unsigned i=0;i<features;++i)if(!borders[i].empty())active_features.push_back(i);
  const unsigned limits[]={64,128,256,512};
  for(int level=0;level<4;++level)if(limits[level]<count){auto q=std::make_unique<PrefixQuantizer>();for(unsigned i=0;i<limits[level];++i)for(auto split:raw[i].split)q->border[split.first].push_back(split.second);
   for(int i=0;i<features;++i){auto&b=q->border[i];std::sort(b.begin(),b.end());b.erase(std::unique(b.begin(),b.end()),b.end());for(float threshold:b)q->rank[i].push_back(std::lower_bound(borders[i].begin(),borders[i].end(),threshold)-borders[i].begin());q->rank[i].push_back(borders[i].size());}prefix_quantizer[level]=std::move(q);}
  for(auto&r:raw){Tree t;for(auto s:r.split)t.split.push_back({uint16_t(s.first),uint16_t(std::lower_bound(borders[s.first].begin(),borders[s.first].end(),s.second)-borders[s.first].begin())});t.leaf=std::move(r.leaf);trees.push_back(std::move(t));}

 }
 Distance predict(Node source,Node target,Distance lower,const PhaseLowerBound&bounds)const {
  if(obstacle_phase)throw std::runtime_error("Obstacle-phase model requires template correction entry");
  if(source==target)return 0;auto x=expand(feature_builder->get(source,target,lower,bounds),source,target);
  return Distance(std::nearbyint(double(lower)+std::max(0.,100*value(x))));
 }
 Distance correct_template(Node source,Node target,Distance base,float vg,float hg,unsigned count=UINT_MAX)const{
  if(source==target)return 0;
  auto x=expand(feature_builder->get(source,target,base,vg,hg),source,target);
  if(obstacle_phase){x[27]=archdata::SITES[source/496].y%100;x[28]=archdata::SITES[target/496].y%100;}
  return Distance(std::nearbyint(std::max(0.,double(base)+100*value(x,count))));
 }
};
