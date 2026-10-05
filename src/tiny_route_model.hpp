#pragma once
#include "fast_architecture_features.hpp"
#include <cstring>
// Learned min-plus experts are approximations, not feasible-path certificates.
class TinyRouteModel {
    unsigned hidden=0,routes=0;bool factorized=false,joint_phase=false;
    std::array<float,71>mean{},scale{};
    struct Layer {unsigned in,out;std::vector<float>weight,bias;};
    std::array<Layer,3>layer;
    std::vector<float>source_phase,target_phase,source_factor,target_factor,sx,sy,tx,ty;
    FastArchitectureFeatures features;
    static void dense(const float* __restrict__ input,const float* __restrict__ weight,
                      const float* __restrict__ bias,float* __restrict__ output,
                      unsigned in,unsigned out,bool relu){
        std::memcpy(output,bias,out*sizeof(float));
        // Vectorize independent output channels; no floating-point reduction across them.
        for(unsigned c=0;c<in;++c){float value=input[c];const float* __restrict__ column=weight+c*out;
            for(unsigned r=0;r<out;++r)output[r]+=value*column[r];
        }
        if(relu)for(unsigned r=0;r<out;++r)output[r]=std::max(0.f,output[r]);
    }
public:
    explicit TinyRouteModel(const std::string&path):features(true){
        std::ifstream f(path,std::ios::binary);auto read=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),n))throw std::runtime_error("Truncated tiny route model");};
        char magic[8],hash[64];uint32_t shape[3];read(magic,8);read(hash,64);read(shape,12);
        joint_phase=std::string(magic,8)=="TINYROU3";factorized=joint_phase || std::string(magic,8)=="TINYROU2";
        if((std::string(magic,8)!="TINYROU1" && !factorized) || std::string(hash,64)!=archdata::HASH || shape[0]!=71 || (shape[1]!=32 && shape[1]!=64 && shape[1]!=128) || (shape[2]!=64 && shape[2]!=128 && shape[2]!=256 && shape[2]!=512))throw std::runtime_error("Invalid tiny route model");
        hidden=shape[1];routes=shape[2];read(mean.data(),71*4);read(scale.data(),71*4);
        for(unsigned i=0;i<71;++i){if(!std::isfinite(mean[i]) || !std::isfinite(scale[i]) || scale[i]<=0)throw std::runtime_error("Invalid tiny normalization");scale[i]=1/scale[i];}
        const unsigned dims[]={71,hidden,hidden,routes};
        for(int k=0;k<3;++k){auto&l=layer[k];l.in=dims[k];l.out=dims[k+1];l.weight.resize(l.in*l.out);l.bias.resize(l.out);read(l.weight.data(),l.weight.size()*4);read(l.bias.data(),l.bias.size()*4);for(float v:l.weight)if(!std::isfinite(v))throw std::runtime_error("Non-finite tiny weight");for(float v:l.bias)if(!std::isfinite(v))throw std::runtime_error("Non-finite tiny bias");}
        if(!factorized){
        for(auto*table:{&source_phase,&target_phase}){float step;read(&step,4);if(!std::isfinite(step) || step<=0)throw std::runtime_error("Invalid tiny phase scale");std::vector<int16_t>q(496*120*routes);read(q.data(),q.size()*2);table->resize(q.size());for(size_t i=0;i<q.size();++i)(*table)[i]=float(q[i])*step;}
        }else if(joint_phase){
            std::vector<float>*arrays[]={&source_phase,&target_phase,&source_factor,&target_factor,&sx,&tx};
            const size_t sizes[]={496*routes,496*routes,496*8,496*8,120*8*routes,120*8*routes};
            for(int k=0;k<6;++k){arrays[k]->resize(sizes[k]);read(arrays[k]->data(),sizes[k]*4);for(float v:*arrays[k])if(!std::isfinite(v))throw std::runtime_error("Non-finite joint phase factor");}
        }else{
            std::vector<float>*arrays[]={&source_phase,&target_phase,&source_factor,&target_factor,&sx,&sy,&tx,&ty};
            const size_t sizes[]={496*routes,496*routes,496*8,496*8,10*8*routes,12*8*routes,10*8*routes,12*8*routes};
            for(int k=0;k<8;++k){arrays[k]->resize(sizes[k]);read(arrays[k]->data(),sizes[k]*4);for(float v:*arrays[k])if(!std::isfinite(v))throw std::runtime_error("Non-finite phase factor");}
        }
        if(f.get()!=std::char_traits<char>::eof())throw std::runtime_error("Trailing tiny model data");
    }
    Distance predict(Node source,Node target,Distance lower,const PhaseLowerBound&bounds)const{
        if(source==target)return 0;auto x=features.get(source,target,lower,bounds);auto mod=[](int n,int p){return (n%p+p)%p;};
        unsigned phase=mod(int(x[33]),10)*12+mod(int(x[34]),12);
        for(unsigned i=0;i<71;++i)x[i]=std::clamp((x[i]-mean[i])*scale[i],-10.f,10.f);
        alignas(64) std::array<float,512>a{},b{},c{};
        dense(x.data(),layer[0].weight.data(),layer[0].bias.data(),a.data(),71,hidden,true);
        dense(a.data(),layer[1].weight.data(),layer[1].bias.data(),b.data(),hidden,hidden,true);
        dense(b.data(),layer[2].weight.data(),layer[2].bias.data(),c.data(),hidden,routes,false);
        float gap=std::numeric_limits<float>::infinity();
        if(!factorized){
            const float*s=source_phase.data()+((source%496)*120+phase)*routes;
            const float*t=target_phase.data()+((target%496)*120+phase)*routes;
            for(unsigned r=0;r<routes;++r)gap=std::min(gap,(c[r]+s[r])+t[r]);
        }else if(joint_phase){
            alignas(64) std::array<float,512>zero{};
            const float*s=source_phase.data()+(source%496)*routes;
            const float*t=target_phase.data()+(target%496)*routes;
            dense(source_factor.data()+(source%496)*8,sx.data()+phase*8*routes,zero.data(),a.data(),8,routes,false);
            dense(target_factor.data()+(target%496)*8,tx.data()+phase*8*routes,zero.data(),b.data(),8,routes,false);
            for(unsigned r=0;r<routes;++r)gap=std::min(gap,(((c[r]+s[r])+t[r])+a[r])+b[r]);
        }else{
            alignas(64) std::array<float,512>zero{};
            const float*s=source_phase.data()+(source%496)*routes;
            const float*t=target_phase.data()+(target%496)*routes;
            dense(source_factor.data()+(source%496)*8,sx.data()+(phase/12)*8*routes,zero.data(),a.data(),8,routes,false);
            dense(source_factor.data()+(source%496)*8,sy.data()+(phase%12)*8*routes,zero.data(),b.data(),8,routes,false);
            for(unsigned r=0;r<routes;++r)c[r]+=s[r]+(a[r]+b[r]);
            dense(target_factor.data()+(target%496)*8,tx.data()+(phase/12)*8*routes,zero.data(),a.data(),8,routes,false);
            dense(target_factor.data()+(target%496)*8,ty.data()+(phase%12)*8*routes,zero.data(),b.data(),8,routes,false);
            for(unsigned r=0;r<routes;++r)gap=std::min(gap,c[r]+(t[r]+(a[r]+b[r])));
        }
        return Distance(std::nearbyint(double(lower)+double(std::max(0.f,100.f*gap))));
    }
};
