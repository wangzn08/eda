#pragma once
#include "architecture_data.hpp"
#include <array>
#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include "potential_lower_model.hpp"
#include <cmath>
#include <fstream>
#include <map>
#include <limits>
#include <string>
#include <vector>

// Small learned route model; its latent routes are not path certificates.
class PhaseRouteModel {
    std::map<std::string,std::vector<float>> weights;
    std::vector<float> mean,scale;
    uint32_t kind=1,numeric=89,routes=64;
    float tau=0;
    double teacher_weight=0;
    const std::vector<float>& tensor(const std::string& name,size_t expected) const {
        auto it=weights.find(name);if(it==weights.end() || it->second.size()!=expected)throw std::runtime_error("Invalid neural tensor "+name);return it->second;
    }
    static std::vector<float> dense(const std::vector<float>& x,const std::vector<float>& w,const std::vector<float>& b,bool activation) {
        std::vector<float> out(b.size());
        for(size_t r=0;r<out.size();++r) {
            float sum=b[r];for(size_t c=0;c<x.size();++c)sum+=w[r*x.size()+c]*x[c];
            out[r]=activation?sum/(1.f+std::exp(-sum)):sum;
        }
        return out;
    }
public:
    explicit PhaseRouteModel(const std::string& path) {
        std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("Cannot open neural model");
        auto read=[&](void* p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated neural model");};
        char magic[8];read(magic,8);if(std::string(magic,8)!=std::string("ROUTENN1",8))throw std::runtime_error("Bad neural magic");
        uint32_t version,count;read(&version,4);if(version!=1)throw std::runtime_error("Bad neural version");
        read(&kind,4);read(&numeric,4);read(&routes,4);
        if(kind<1 || kind>3 || numeric!=(kind==2?93u:89u) || (routes!=64 && routes!=128))throw std::runtime_error("Bad neural shape");
        mean.resize(numeric);scale.resize(numeric);
        read(&tau,4);read(&teacher_weight,8);read(mean.data(),mean.size()*4);read(scale.data(),scale.size()*4);read(&count,4);
        if(count>32 || !(tau>0) || !(teacher_weight>=0 && teacher_weight<=1))throw std::runtime_error("Invalid neural configuration");
        for(uint32_t i=0;i<count;++i) {
            uint32_t length,n;read(&length,4);if(length>100)throw std::runtime_error("Bad tensor name");
            std::string name(length,'\0');read(name.data(),length);read(&n,4);if(n>1000000)throw std::runtime_error("Bad neural tensor size");
            auto& v=weights[name];if(!v.empty())throw std::runtime_error("Duplicate tensor");v.resize(n);read(v.data(),n*4);
            for(float value:v)if(!std::isfinite(value))throw std::runtime_error("Non-finite neural parameter");
        }
        for(size_t i=0;i<numeric;++i)if(!std::isfinite(mean[i]) || !std::isfinite(scale[i]) || scale[i]<=0)throw std::runtime_error("Bad normalization");
        tensor("s.weight",496*routes);tensor("t.weight",496*routes);tensor("graph",496*32);
        if(kind==1) {tensor("phase_source.weight",496*8);tensor("phase_target.weight",496*8);
            for(auto name:{"sx","tx"})tensor(name,10*8*routes);for(auto name:{"sy","ty"})tensor(name,12*8*routes);}
        tensor("geo.0.weight",256*(numeric+64));tensor("geo.0.bias",256);tensor("geo.2.weight",256*256);tensor("geo.2.bias",256);tensor("geo.4.weight",routes*256);tensor("geo.4.bias",routes);
    }
    static uint64_t lower_bound(const std::array<float,73>& original,archdata::XY source,archdata::XY target) {
        auto phi=[](int x){return x-std::clamp(x-76,0,14);};int dx=phi(target.x)-phi(source.x),dy=target.y-source.y;
        int sp=int(original[10]),tp=int(original[11]);int64_t result=0;
        for(size_t k=0;k<4;++k) {int64_t value=int64_t(potential_lower_model::ax[k])*dx+int64_t(potential_lower_model::ay[k])*dy+potential_lower_model::distance[k*archdata::P*archdata::P+sp*archdata::P+tp];result=std::max(result,(value+11)/12);}
        return uint64_t(result)+uint64_t(original[20])+uint64_t(original[21]);
    }
    uint64_t predict(const std::array<float,73>& original,archdata::XY source,archdata::XY target,uint64_t baseline,uint64_t upper,uint64_t teacher) const {
        std::vector<float> raw(numeric);std::copy(original.begin(),original.end(),raw.begin());bool available=upper<std::numeric_limits<uint64_t>::max()/4;
        raw[73]=available?float(upper):0;raw[74]=available?1.f:0.f;
        raw[75]=available?float(double(upper)/std::max(1.,double(baseline))):0;raw[76]=available?float(double(upper)-double(baseline)):0;
        uint64_t lower=lower_bound(original,source,target);
        if(kind==2) {raw[77]=float(lower);raw[78]=float(double(lower)/std::max(1.,double(baseline)));raw[79]=available?float(double(upper)-double(lower)):0;raw[80]=available?float((double(upper)-double(lower))/std::max(1.,double(baseline))):0;}
        const unsigned period_start=kind==2?81:77;
        const int ix[]={35,36,0,1,2,3},period[]={10,12,10,12,10,12};
        for(size_t k=0;k<6;++k) {float angle=raw[ix[k]]*float(6.2831853071795864769/period[k]);raw[period_start+2*k]=std::sin(angle);raw[period_start+1+2*k]=std::cos(angle);}
        std::vector<float> input(numeric+64);for(size_t i=0;i<numeric;++i)input[i]=std::clamp((raw[i]-mean[i])/scale[i],-10.f,10.f);
        int sp=int(raw[10]),tp=int(raw[11]);const auto& graph=tensor("graph",496*32);
        for(int i=0;i<32;++i) {input[numeric+i]=graph[sp*32+i];input[numeric+32+i]=graph[tp*32+i];}
        auto a=dense(input,tensor("geo.0.weight",256*(numeric+64)),tensor("geo.0.bias",256),true);
        auto b=dense(a,tensor("geo.2.weight",256*256),tensor("geo.2.bias",256),true);
        auto costs=dense(b,tensor("geo.4.weight",routes*256),tensor("geo.4.bias",routes),false);
        const auto& se=tensor("s.weight",496*routes);const auto& te=tensor("t.weight",496*routes);
        std::vector<float> phase(routes,0);
        if(kind==1) {
            const auto& ps=tensor("phase_source.weight",496*8);const auto& pt=tensor("phase_target.weight",496*8);
            int rx=(int(raw[35])%10+10)%10,ry=(int(raw[36])%12+12)%12;
            const auto& sx=tensor("sx",10*8*routes);const auto& sy=tensor("sy",12*8*routes);const auto& tx=tensor("tx",10*8*routes);const auto& ty=tensor("ty",12*8*routes);
            for(unsigned k=0;k<routes;++k) {
                float px=0,py=0,qx=0,qy=0;
                for(int r=0;r<8;++r) {px+=ps[sp*8+r]*sx[(rx*8+r)*routes+k];py+=ps[sp*8+r]*sy[(ry*8+r)*routes+k];qx+=pt[tp*8+r]*tx[(rx*8+r)*routes+k];qy+=pt[tp*8+r]*ty[(ry*8+r)*routes+k];}
                phase[k]=px+py;phase[k]+=qx+qy;
            }
        }
        float highest=-INFINITY;std::vector<float> exponent(routes);
        for(unsigned k=0;k<routes;++k) {costs[k]=se[sp*routes+k]+te[tp*routes+k]+costs[k]+phase[k];exponent[k]=-costs[k]/tau;highest=std::max(highest,exponent[k]);}
        double sum=0;for(float value:exponent)sum+=std::exp(double(value-highest));
        float gap=-tau*float(double(highest)+std::log(sum))+tau*float(std::log(double(routes)));
        auto phi=[](int x){return x-std::clamp(x-76,0,14);};
        float anchor=12.5f*float(std::abs(phi(target.x)-phi(source.x)))+float(125./12)*float(std::abs(target.y-source.y));anchor+=raw[20];anchor+=raw[21];
        double delay;
        if(kind==2) {gap=std::max(gap,0.f)+std::log1p(std::exp(-std::abs(gap)));delay=double(lower)+double(100.f*gap);}
        else delay=double(std::max(0.f,anchor+100.f*gap));
        uint64_t neural=std::min(upper,uint64_t(std::nearbyint(delay)));
        if(source.x==target.x && source.y==target.y && sp==tp)neural=0;
        uint64_t result=std::min(upper,uint64_t(std::max(0.,std::nearbyint((1-teacher_weight)*double(neural)+teacher_weight*double(teacher)))));
        return kind==2?std::max(lower,result):result;
    }
};
