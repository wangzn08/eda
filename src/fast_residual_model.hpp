#pragma once
#include "routing_search.hpp"
#include <memory>
#include "fast_architecture_features.hpp"
class FastResidualModel {
 struct Split{uint16_t feature,border;};struct Tree{std::vector<Split>split;std::vector<double>leaf;};
 std::vector<Tree>trees;static constexpr int features=71;std::array<std::vector<float>,features>borders;double scale=1,bias=0;
 std::unique_ptr<FastArchitectureFeatures>feature_builder;
public:
 explicit FastResidualModel(const std::string&path,unsigned count){
  std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated residual model");};char magic[8];uint32_t total;read(magic,8);read(&total,4);read(&scale,8);read(&bias,8);if(std::string(magic,8)!="FASTRES1" || !count || count>total || total>4096)throw std::runtime_error("Invalid residual model");
  struct Raw{std::vector<std::pair<uint32_t,float>>split;std::vector<double>leaf;};std::vector<Raw>raw(count);
  for(auto&t:raw){uint32_t depth;read(&depth,4);if(depth>12)throw std::runtime_error("Invalid residual depth");for(unsigned i=0;i<depth;++i){uint32_t feature;float border;read(&feature,4);read(&border,4);if(feature>=features || !std::isfinite(border))throw std::runtime_error("Invalid residual split");t.split.push_back({feature,border});borders[feature].push_back(border);}t.leaf.resize(1u<<depth);read(t.leaf.data(),t.leaf.size()*8);}
  bool needs_topology=false;for(int i=29;i<features;++i)needs_topology|=!borders[i].empty();feature_builder=std::make_unique<FastArchitectureFeatures>(needs_topology);
  for(auto&b:borders){std::sort(b.begin(),b.end());b.erase(std::unique(b.begin(),b.end()),b.end());}
  for(auto&r:raw){Tree t;for(auto s:r.split)t.split.push_back({uint16_t(s.first),uint16_t(std::lower_bound(borders[s.first].begin(),borders[s.first].end(),s.second)-borders[s.first].begin())});t.leaf=std::move(r.leaf);trees.push_back(std::move(t));}

 }
 Distance predict(Node source,Node target,Distance lower,const PhaseLowerBound&bounds)const {
  if(source==target)return 0;auto x=feature_builder->get(source,target,lower,bounds);
  std::array<uint16_t,features>bin;for(int i=0;i<features;++i)bin[i]=std::lower_bound(borders[i].begin(),borders[i].end(),x[i])-borders[i].begin();double value=0;
  for(const auto&t:trees){unsigned leaf=0;for(size_t k=0;k<t.split.size();++k)leaf|=unsigned(bin[t.split[k].feature]>t.split[k].border)<<k;value+=t.leaf[leaf];}
  value=scale*value+bias;return Distance(std::nearbyint(double(lower)+std::max(0.,100*value)));
 }
};
