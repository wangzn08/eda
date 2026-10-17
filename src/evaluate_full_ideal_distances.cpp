// Architecture-only full finite ideal distances at every requested displacement.
// Uses request coordinates and initial legal branch costs from BELLST01, and
// deliberately ignores its base/expanded teacher values. No golden data input.
#include "routing_search.hpp"
#include <fstream>
#include <iostream>
#include <ctime>
struct IdealEdge {int to,dx,dy,cost;};
struct IdealStateRecord {uint32_t row;uint16_t sx,sy,tx,ty,core,target;int32_t entry,unused_base,unused_expanded;};
static_assert(sizeof(IdealStateRecord)==28);
struct IdealSelection {uint16_t sx=65535,sy=65535,tx=65535,ty=65535,core=65535,end=65535,target=65535,kind=65535;int32_t entry=0,nominal=0,terminal=0;};
static_assert(sizeof(IdealSelection)==28);
int main(int argc,char**argv){try{
 if(argc!=4&&argc!=5)throw std::runtime_error("Teacher states, local costs, prediction binary, optional full raw curve output required");Graph graph;
 std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::array<uint16_t,160>ports;unsigned count=0;
 for(unsigned k=0;k<std::size(archdata::NETS);++k){auto n=archdata::NETS[k];index[n.to]=count;ports[count++]=n.to;netout[n.from]=k;}if(count!=160)throw std::runtime_error("Core count");
 std::array<std::vector<IdealEdge>,160>edges;std::array<std::vector<std::pair<unsigned,unsigned>>,496>terminal;
 for(unsigned k=0;k<160;++k)terminal[ports[k]].push_back({k,0});
 for(auto a:archdata::ARCS){if(index[a.from]>=0)terminal[a.to].push_back({unsigned(index[a.from]),unsigned(a.delay)});if(index[a.from]>=0&&netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay});}}
 std::array<int,120>xgap{};std::array<int,550>ygap{};for(auto l:archdata::LINES){if(l.vertical)for(int x=l.site+1;x<120;++x)xgap[x]+=l.delay;else for(int y=l.site+1;y<550;++y)ygap[y]+=l.delay;}
 std::array<int,120*550>grid;grid.fill(-1);for(unsigned i=0;i<std::size(archdata::SITES);++i){auto s=archdata::SITES[i];grid[s.x*550+s.y]=i;}
 std::ifstream sf(argv[1],std::ios::binary);char magic[8],hash[64];uint32_t size;sf.read(magic,8);sf.read(hash,64);sf.read(reinterpret_cast<char*>(&size),4);if(std::string(magic,8)!="BELLST01"||std::string(hash,64)!=archdata::HASH||size!=28)throw std::runtime_error("State header");std::array<std::vector<IdealStateRecord>,160>states;IdealStateRecord record;uint64_t records=0;
 while(sf.read(reinterpret_cast<char*>(&record),28)){if(record.core>=160||record.target>=496||record.sx>=120||record.tx>=120||record.sy>=550||record.ty>=550)throw std::runtime_error("Record coordinates");states[record.core].push_back(record);++records;}if(!sf.eof())throw std::runtime_error("State input");
 std::ifstream lf(argv[2],std::ios::binary);lf.seekg(0,std::ios::end);auto bytes=lf.tellg();if(bytes<=0||bytes%4)throw std::runtime_error("Local file length");lf.seekg(0);std::vector<int32_t>predictions(size_t(bytes)/4);lf.read(reinterpret_cast<char*>(predictions.data()),bytes);if(!lf)throw std::runtime_error("Local file input");
 constexpr int RX=156,RY=624,WX=313,WY=1249,limit=9000;auto state=[](int x,int y,int p){return ((x+RX)*WY+y+RY)*160+p;};std::vector<uint16_t>d(size_t(WX)*WY*160);std::vector<std::vector<uint32_t>>buckets(limit);auto begin=std::clock();
 std::vector<IdealSelection>selections(predictions.size());std::ofstream curves;std::vector<int16_t>slab;
 if(argc==5){curves.open(argv[4],std::ios::binary);if(!curves)throw std::runtime_error("Curve output");curves.write("FDCRAW01",8);curves.write(archdata::HASH,64);curves.write(reinterpret_cast<char*>(ports.data()),320);uint32_t shape[6]={160,160,239,24,46,2};curves.write(reinterpret_cast<char*>(shape),24);slab.resize(size_t(160)*239*24*46);}
 for(unsigned si=0;si<160;++si){std::fill(d.begin(),d.end(),65535);for(auto&b:buckets)b.clear();d[state(0,0,si)]=0;buckets[0].push_back(state(0,0,si));
  for(int cost=0;cost<limit;++cost)for(size_t j=0;j<buckets[cost].size();++j){auto u=buckets[cost][j];if(d[u]!=cost)continue;int x=int(u/160)/WY-RX,y=int(u/160)%WY-RY;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -RX||nx>RX||ny < -RY||ny>RY||value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value].push_back(v);}}}
  for(auto r:states[si]){if(r.row>=predictions.size())throw std::runtime_error("Row id");int dx=int(r.tx)-r.sx,dy=int(r.ty)-r.sy;auto site=grid[r.tx*550+r.ty];if(site<0)throw std::runtime_error("Target site");uint32_t mask=graph.reverse_vector_mask(site);bool cross=std::min(r.sx,r.tx)<76&&std::max(r.sx,r.tx)>89,blocked=false;if(cross)for(auto b:archdata::BLOCKS)if(b.left==76&&b.right==89&&r.sy>=b.lower&&r.sy<=b.upper&&r.ty>=b.lower&&r.ty<=b.upper)blocked=true;
   int best=1000000000;unsigned chosen=65535,cost=0,kind=0;for(auto end:terminal[r.target]){if(!(mask&(1u<<archdata::NETS[end.first].vector))&&!(dx==0&&dy==0&&si==end.first))continue;if(!blocked){auto value=d[state(dx,dy,end.first)];if(value!=65535&&int(value)+int(end.second)<best){best=int(value)+int(end.second);chosen=end.first;cost=end.second;kind=0;}}if(cross){auto value=d[state(dx+(dx>0?-14:14),dy,end.first)];if(value!=65535&&int(value)+int(end.second)+292<best){best=int(value)+int(end.second)+292;chosen=end.first;cost=end.second;kind=2;}}}
   if(best<1000000000){int value=best+r.entry+std::abs(xgap[r.sx]-xgap[r.tx])+std::abs(ygap[r.sy]-ygap[r.ty]);if(value<predictions[r.row]){predictions[r.row]=value;selections[r.row]={r.sx,r.sy,r.tx,r.ty,uint16_t(si),uint16_t(chosen),r.target,uint16_t(kind),r.entry,best,int32_t(cost)};}}
  }
  if(argc==5){size_t pos=0;for(unsigned ti=0;ti<160;++ti)for(int x=-119;x<=119;++x)for(int sign:{-1,1})for(int r=0;r<12;++r)for(int q=0;q<46;++q){int truth=d[state(x,sign*(12*q+r),ti)];if(truth==65535)throw std::runtime_error("Unreachable full curve");int qx=std::abs(x)>29?(std::abs(x)-20)/10:0,value=truth-qx*125-q*(sign>0?127:125);if(value<-32768||value>32767)throw std::runtime_error("Full curve overflow");slab[pos++]=int16_t(value);}if(pos!=slab.size())throw std::runtime_error("Curve count");curves.write(reinterpret_cast<char*>(slab.data()),slab.size()*2);if(!curves)throw std::runtime_error("Curve write");}
  std::cerr<<"source="<<si<<" states="<<states[si].size()<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';
 }
 for(auto p:predictions)if(p<0||p>=1000000000)throw std::runtime_error("Unreachable request");std::ofstream out(argv[3],std::ios::binary);out.write(reinterpret_cast<char*>(predictions.data()),predictions.size()*4);if(!out)throw std::runtime_error("Prediction output");std::cerr<<"rows="<<predictions.size()<<" states="<<records<<" bytes="<<uint64_t(out.tellp())<<'\n';
 std::ofstream selected(std::string(argv[3])+".selected",std::ios::binary);selected.write("FULSEL01",8);selected.write(archdata::HASH,64);uint32_t shape[2]={uint32_t(selections.size()),28};selected.write(reinterpret_cast<char*>(shape),8);selected.write(reinterpret_cast<char*>(selections.data()),selections.size()*28);if(!selected)throw std::runtime_error("Selection output");if(argc==5)std::cerr<<"curve_bytes="<<uint64_t(curves.tellp())<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
