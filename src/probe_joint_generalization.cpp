// Independent nominal Dijkstra vs additive directional transient model.
#include "core_template_model.hpp"
#include <array>
#include <vector>
#include <fstream>
#include <iostream>
struct Stats{uint64_t n=0,exact=0;int64_t signed_sum=0;uint64_t abs_sum=0;void add(int64_t e){++n;exact+=e==0;signed_sum+=e;abs_sum+=std::llabs(e);}};
struct ProbeEdge {int to,dx,dy,cost;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("Expected output csv");
 CoreTemplateModel model("out/architecture-benchmark/core-template-xz6.bin",false,0,0,"out/architecture-benchmark/vertical-transients-xz.bin",UINT_MAX,"out/architecture-benchmark/horizontal-transients.bin","out/architecture-benchmark/vertical-distant-delta-xz6.bin");
 std::array<int,496>index,netout;index.fill(-1);netout.fill(-1);std::vector<int>ports;
 for(unsigned i=0;i<std::size(archdata::NETS);++i){auto n=archdata::NETS[i];index[n.to]=ports.size();ports.push_back(n.to);netout[n.from]=i;}
 std::vector<std::vector<ProbeEdge>>edges(160);
 for(auto a:archdata::ARCS)if(index[a.from]>=0 && netout[a.to]>=0){auto n=archdata::NETS[netout[a.to]];auto v=archdata::VECTORS[n.vector];edges[index[a.from]].push_back({index[n.to],v.x,v.y,a.delay+n.delay});}
 constexpr int R=144,W=289,limit=5000;auto state=[](int x,int y,int p){return ((x+R)*W+y+R)*160+p;};
 std::vector<uint16_t>d(W*W*160);std::vector<std::vector<uint32_t>>buckets(limit);
 std::ifstream patch("out/architecture-benchmark/joint-transient.raw.bin",std::ios::binary);char header[392];patch.read(header,392);if(!patch || std::string(header,8)!="TRJRAW01" || std::string(header+8,64)!=archdata::HASH)throw std::runtime_error("Patch header mismatch");std::vector<int16_t>delta(160*160*480);patch.read(reinterpret_cast<char*>(delta.data()),delta.size()*2);if(!patch)throw std::runtime_error("Patch truncated");
 int xs[4]={1,3,5,7},ys[4]={2,4,6,8};Stats stats[4][4][5];
 std::ofstream out(argv[1]);if(!out)throw std::runtime_error("Output open failed");
 for(int si:{0,80,159}){
  std::fill(d.begin(),d.end(),65535);for(auto& b:buckets)b.clear();d[state(0,0,si)]=0;buckets[0].push_back(state(0,0,si));
  for(int cost=0;cost<limit;++cost)for(size_t j=0;j<buckets[cost].size();++j){auto u=buckets[cost][j];if(d[u]!=cost)continue;int x=int(u/160)/W-R,y=int(u/160)%W-R;for(auto e:edges[u%160]){int nx=x+e.dx,ny=y+e.dy,value=cost+e.cost;if(nx < -R || nx>R || ny < -R || ny>R || value>=limit)continue;auto v=state(nx,ny,e.to);if(value<d[v]){d[v]=value;buckets[value].push_back(v);}}}
  for(int ti=0;ti<160;++ti)for(unsigned sx=0;sx<2;++sx)for(unsigned sy=0;sy<2;++sy)for(int rx=0;rx<10;++rx)for(int ry=0;ry<12;++ry)for(unsigned xi=0;xi<4;++xi)for(unsigned yi=0;yi<4;++yi){
   int qx=xs[xi],qy=ys[yi],dx=(sx?1:-1)*(20+10*qx+rx),dy=(sy?1:-1)*(24+12*qy+ry);int truth=d[state(dx,dy,ti)];if(truth==65535)throw std::runtime_error("Unreachable probe");
   int64_t prediction=model.direct_nominal_probe(ports[si],ports[ti],dx,dy);int corr=delta[((si*160+ti)*4+sx*2+sy)*120+rx*12+ry];
   int wx=std::min(qx,5),wy=std::min(qy,6),fade=std::min(std::min(qx-1,4)*5,std::min(qy-1,5)*4);
   int corrections[5]={0,corr,corr*std::min(wx*6,wy*5)/30,corr*wx*wy/30,corr*fade/20};
   for(unsigned method=0;method<5;++method)stats[xi][yi][method].add(prediction+corrections[method]-truth);
  }
  std::cerr<<"source="<<si<<" complete\n";
 }
 out<<"qx,qy,method,rows,mean_absolute_error_ps,mean_signed_error_ps,exact_fraction\n";
 for(unsigned xi=0;xi<4;++xi)for(unsigned yi=0;yi<4;++yi)for(unsigned method=0;method<5;++method){auto v=stats[xi][yi][method];out<<xs[xi]<<','<<ys[yi]<<','<<method<<','<<v.n<<','<<double(v.abs_sum)/v.n<<','<<double(v.signed_sum)/v.n<<','<<double(v.exact)/v.n<<'\n';}
 if(!out)throw std::runtime_error("Output write failed");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
