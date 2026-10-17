#include "core_template_model.hpp"
#include "fast_residual_model.hpp"
#include <filesystem>
#include "buffered_csv_writer.hpp"
#include "buffered_csv_reader.hpp"
#ifndef CORE_LOAD_HINT_ASSETS
#define CORE_LOAD_HINT_ASSETS 0
#endif
#ifndef CORE_DEFAULT_ADAPTIVE_SOURCES
#define CORE_DEFAULT_ADAPTIVE_SOURCES 0
#endif
#ifndef CORE_BENCHMARK_SPLIT
#define CORE_BENCHMARK_SPLIT 0
#endif
#ifndef CORE_ZERO_COPY_BATCH
#define CORE_ZERO_COPY_BATCH 0
#endif
#ifndef CORE_ROUTE_TRACE
#define CORE_ROUTE_TRACE 0
#endif
#ifndef CORE_PREPARED
#define CORE_PREPARED 0
#endif
#ifndef CORE_RING_PIPELINE
#define CORE_RING_PIPELINE 0
#endif
#ifndef CORE_BATCH_SIZE
#define CORE_BATCH_SIZE 0
#endif
#ifndef CORE_BUFFERED_INPUT
#define CORE_BUFFERED_INPUT 0
#endif
static_assert(!CORE_ZERO_COPY_BATCH || (CORE_BUFFERED_INPUT && !CORE_RING_PIPELINE),"Zero-copy batches require buffered input and no ring");
#include <ctime>
#include <iostream>
#ifndef CORE_FAST12_PROFILE
#define CORE_FAST12_PROFILE 0
#endif
#ifndef CORE_FAST12_TARGET
#define CORE_FAST12_TARGET 0
#endif
#ifndef CORE_FAST15_PROFILE
#define CORE_FAST15_PROFILE 0
#endif
#ifndef CORE_FAST30_PROFILE
#define CORE_FAST30_PROFILE 0
#endif
#ifndef CORE_DEFAULT_TREES
#define CORE_DEFAULT_TREES 256
#endif
#ifndef CORE_DEFAULT_JOINT
#define CORE_DEFAULT_JOINT 0
#endif
std::string_view strip(std::string_view s){auto a=s.find_first_not_of(" \r\n\t"),b=s.find_last_not_of(" \r\n\t");return a==s.npos?std::string_view{}:s.substr(a,b-a+1);}
int main(int argc,char**argv){try{
 // Research profiles may provide a matching signed correction beside the executable.
 auto directory=std::filesystem::absolute(argv[0]).parent_path();std::string descriptor_path,export_hints,source_hint_asset=CORE_LOAD_HINT_ASSETS?(directory/"source-hints.bin").string():"",horizontal_hint_asset=CORE_LOAD_HINT_ASSETS?(directory/"horizontal-hints.bin").string():"",input,output,residual,transient,horizontal,far,interaction,model=(directory/"core-template.bin").string();unsigned all_corridors=0;unsigned adaptive_sources=CORE_DEFAULT_ADAPTIVE_SOURCES;unsigned source_hints=CORE_FAST15_PROFILE?8:0;unsigned terminal_hints=CORE_FAST30_PROFILE?1:0,corridor_hubs=CORE_FAST30_PROFILE?1:0,growth_cap=UINT_MAX,shell_x=0,shell_y=0,trees=CORE_DEFAULT_TREES,near_distance=50,middle_distance=150,far_trees=256;bool paired_terminal=false;bool target_horizontal=CORE_FAST12_TARGET;bool fused_horizontal=CORE_FAST12_PROFILE;bool scan_coordinates=CORE_FAST15_PROFILE;bool horizontal_hints=CORE_FAST15_PROFILE;bool packed_ports=CORE_FAST15_PROFILE;bool grammar_ports=false;bool exact_near_hints=CORE_FAST30_PROFILE;bool perfect_ports=false;bool integer_bins=false;bool buffered_output=CORE_FAST30_PROFILE;bool corridor=CORE_FAST30_PROFILE;bool wide_joint=CORE_FAST30_PROFILE;bool joint_layout=CORE_DEFAULT_JOINT || CORE_FAST30_PROFILE;bool adaptive=false;bool use_cache=false,progress=false,envelope=false;
 if(CORE_FAST15_PROFILE){if(std::filesystem::exists(directory/"source-hints.bin"))source_hint_asset=(directory/"source-hints.bin").string();if(std::filesystem::exists(directory/"horizontal-hints.bin"))horizontal_hint_asset=(directory/"horizontal-hints.bin").string();}
 if(CORE_FAST30_PROFILE)interaction=(directory/"joint-interaction.bin").string();
 if(std::filesystem::exists(directory/"vertical-far-delta.bin"))far=(directory/"vertical-far-delta.bin").string();
 if(std::filesystem::exists(directory/"horizontal-transients.bin"))horizontal=(directory/"horizontal-transients.bin").string();
 if(std::filesystem::exists(directory/"vertical-transients.bin"))transient=(directory/"vertical-transients.bin").string();
 if(std::filesystem::exists(directory/"correction.bin"))residual=(directory/"correction.bin").string();
 for(int i=1;i<argc;++i){std::string arg=argv[i];if(arg=="--help"){std::cout<<"core_template_estimate -in requests.csv -out result.csv [--model file] [--vertical-transients file --growth-cap count] [--far-vertical-delta file] [--terminal-hints 1..2 --exact-near-hints] [--source-hints 4|8|16 --horizontal-hints] [--source-hint-asset file --horizontal-hint-asset file] [--scan-coords --packed-ports] [--grammar-ports] [--perfect-ports] [--integer-bins] [--buffered-output] [--joint-interaction file] [--corridor-geometry --corridor-hubs 1..32] [--joint-layout|--wide-joint] [--envelope] [--shell-x 0..2 --shell-y 0..2] [--residual-model file --trees count] [--cache|--no-cache] [--progress]\nApproximate learned predictor; no error certificate.\n";return 0;}
  if(arg=="--paired-terminal"){paired_terminal=true;continue;}if(arg=="--target-horizontal"){target_horizontal=true;fused_horizontal=true;continue;}if(arg=="--fused-horizontal"){fused_horizontal=true;continue;}if(arg=="--scan-coords"){scan_coordinates=true;continue;}if(arg=="--horizontal-hints"){horizontal_hints=true;continue;}if(arg=="--packed-ports"){packed_ports=true;continue;}if(arg=="--grammar-ports"){grammar_ports=true;continue;}if(arg=="--exact-near-hints"){exact_near_hints=true;continue;}if(arg=="--perfect-ports"){perfect_ports=true;continue;}if(arg=="--integer-bins"){integer_bins=true;continue;}if(arg=="--buffered-output"){buffered_output=true;continue;}if(arg=="--corridor-geometry"){corridor=true;continue;}if(arg=="--wide-joint"){wide_joint=true;joint_layout=true;continue;}if(arg=="--joint-layout"){joint_layout=true;continue;}if(arg=="--adaptive-trees"){adaptive=true;continue;}if(arg=="--envelope"){envelope=true;continue;}if(arg=="--no-cache"){use_cache=false;continue;}if(arg=="--cache"){use_cache=true;continue;}if(arg=="--progress"){progress=true;continue;}if(i+1==argc)throw std::runtime_error("Missing argument");
  if(arg=="--all-corridors")all_corridors=std::stoul(argv[++i]);else if(arg=="--descriptor-out")descriptor_path=argv[++i];else if(arg=="-in")input=argv[++i];else if(arg=="-out")output=argv[++i];else if(arg=="--model")model=argv[++i];else if(arg=="--residual-model")residual=argv[++i];else if(arg=="--joint-interaction")interaction=argv[++i];else if(arg=="--export-hints")export_hints=argv[++i];else if(arg=="--source-hint-asset")source_hint_asset=argv[++i];else if(arg=="--horizontal-hint-asset")horizontal_hint_asset=argv[++i];else if(arg=="--adaptive-sources")adaptive_sources=std::stoul(argv[++i]);else if(arg=="--source-hints")source_hints=std::stoul(argv[++i]);else if(arg=="--terminal-hints")terminal_hints=std::stoul(argv[++i]);else if(arg=="--corridor-hubs")corridor_hubs=std::stoul(argv[++i]);else if(arg=="--far-vertical-delta")far=argv[++i];else if(arg=="--horizontal-transients")horizontal=argv[++i];else if(arg=="--vertical-transients")transient=argv[++i];else if(arg=="--growth-cap")growth_cap=std::stoul(argv[++i]);else if(arg=="--shell-x")shell_x=std::stoul(argv[++i]);else if(arg=="--shell-y")shell_y=std::stoul(argv[++i]);else if(arg=="--trees")trees=std::stoul(argv[++i]);else if(arg=="--near-distance")near_distance=std::stoul(argv[++i]);else if(arg=="--middle-distance")middle_distance=std::stoul(argv[++i]);else if(arg=="--far-trees")far_trees=std::stoul(argv[++i]);else throw std::runtime_error("Unknown option");
 }
 if((shell_x || shell_y) && !residual.empty())throw std::runtime_error("Shell candidates require a separately fitted correction; omit residual model");
 if(adaptive && (residual.empty() || envelope || trees!=1024 || !far_trees || far_trees>512 || near_distance>=middle_distance))throw std::runtime_error("Invalid adaptive tree configuration");if(input.empty() || output.empty())throw std::runtime_error("Input and output required");auto normalized=[](const std::string&p){return std::filesystem::weakly_canonical(std::filesystem::absolute(p));};for(auto&p:{input,descriptor_path,model,residual,transient,horizontal,far,interaction,source_hint_asset,horizontal_hint_asset})if(!p.empty() && normalized(output)==normalized(p))throw std::runtime_error("Output must differ from inputs/assets");
 auto begin=std::clock();Graph graph;CoreTemplateModel predictor(model,envelope,shell_x,shell_y,transient,growth_cap,horizontal,far,corridor,interaction);if(joint_layout)predictor.enable_joint_layout();if(wide_joint)predictor.enable_short_vertical_layout();if(corridor_hubs)predictor.enable_corridor_hubs(corridor_hubs);if(fused_horizontal)predictor.enable_horizontal_layout();if(target_horizontal)predictor.enable_target_horizontal_layout();if(terminal_hints)predictor.enable_terminal_hints(terminal_hints,exact_near_hints);if(horizontal_hints)predictor.enable_horizontal_hints(horizontal_hint_asset);if(adaptive_sources)predictor.enable_adaptive_sources(adaptive_sources);if(source_hints)predictor.enable_source_hints(graph,source_hints,source_hint_asset);if(all_corridors)predictor.enable_all_corridors(all_corridors);if(paired_terminal)predictor.enable_paired_terminal();if(!export_hints.empty())predictor.save_hint_assets(export_hints);if(CORE_CORE_PHASE_MAJOR)predictor.enable_core_layout();std::unique_ptr<FastResidualModel>correction;if(!residual.empty())correction=std::make_unique<FastResidualModel>(residual,trees);if(integer_bins && correction)correction->enable_integer_bins();FastPinParser parser;if(scan_coordinates)parser.enable_scan_coordinates();if(packed_ports)parser.enable_packed_port_index();if(grammar_ports)parser.enable_grammar_port_index();if(perfect_ports)parser.enable_perfect_port_index();std::unique_ptr<PredictionCache>cache;if(use_cache)cache=std::make_unique<PredictionCache>();double init=double(std::clock()-begin)/CLOCKS_PER_SEC;
 std::ifstream in;std::unique_ptr<BufferedCsvReader> reader;if(CORE_BUFFERED_INPUT)reader=std::make_unique<BufferedCsvReader>(input);else in.open(input);std::ofstream out;std::unique_ptr<BufferedCsvWriter>writer;if(buffered_output)writer=std::make_unique<BufferedCsvWriter>(output);else out.open(output);std::vector<char>buffer(1<<20);out.rdbuf()->pubsetbuf(buffer.data(),buffer.size());std::string storage;std::string_view line;auto next_line=[&](){if(reader)return reader->next(line);if(!std::getline(in,storage))return false;line=storage;return true;};if((!reader && !in) || (!writer && !out) || !next_line() || strip(line)!="From,To")throw std::runtime_error("Invalid request header");if(!writer)out<<"From,To,delay\n";uint64_t rows=0;
 std::ofstream descriptors;if(!descriptor_path.empty()){if(!CORE_ROUTE_TRACE)throw std::runtime_error("Descriptor output requires a research build");descriptors.open(descriptor_path);if(!descriptors)throw std::runtime_error("Descriptor output open failed");descriptors<<"source_core,target_core,dx,dy,qx,qy,rx,ry,kind,entry_cost,source_x,source_y,margin,nominal_delay,terminal_cost,base0,base1,base2,base3,horizontal_delta,interaction_delta,cell_kind\n";}
 auto process=[&](std::string_view s,std::string_view t,Node from,Node to,const CoreTemplateModel::PreparedRequest*prepared=nullptr){Distance delay=INF;uint64_t key=(uint64_t(from)<<32)|to;
  if(!cache || !cache->get(key,delay)){CoreTemplateModel::RouteTrace info;delay=predictor.predict(graph,from,to,CORE_ROUTE_TRACE && descriptors.is_open()?&info:nullptr,prepared);if(CORE_ROUTE_TRACE && descriptors.is_open())descriptors<<info.source_core<<','<<info.target_core<<','<<info.dx<<','<<info.dy<<','<<info.qx<<','<<info.qy<<','<<info.rx<<','<<info.ry<<','<<info.kind<<','<<info.entry_cost<<','<<info.source_x<<','<<info.source_y<<','<<info.margin<<','<<info.nominal_delay<<','<<info.terminal_cost<<','<<info.base0<<','<<info.base1<<','<<info.base2<<','<<info.base3<<','<<info.horizontal_delta<<','<<info.interaction_delta<<','<<info.cell_kind<<'\n';if(correction && delay<INF){auto gaps=predictor.gap_features(from,to);unsigned count=trees;if(adaptive){auto a=archdata::SITES[from/496],b=archdata::SITES[to/496];unsigned distance=std::abs(a.x-b.x)+std::abs(a.y-b.y);count=distance<near_distance?1024:distance<middle_distance?512:far_trees;}delay=correction->correct_template(from,to,delay,gaps.first,gaps.second,count);}if(cache)cache->put(key,delay);}if(delay>=INF)throw std::runtime_error("Unreachable query");if(writer)writer->row(s,t,delay);else{out.write(s.data(),s.size());out.put(',');out.write(t.data(),t.size());out.put(',');char digits[32];auto end=std::to_chars(digits,digits+32,delay);if(end.ec!=std::errc())throw std::runtime_error("Delay formatting failure");out.write(digits,end.ptr-digits);out.put('\n');}++rows;if(CORE_BENCHMARK_SPLIT && rows==CORE_BENCHMARK_SPLIT)std::cerr<<"checkpoint_cpu_seconds="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<"\n";if(progress && rows%100000==0)std::cerr<<"progress="<<rows<<" cpu="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<'\n';};
 constexpr unsigned batch_capacity=CORE_BATCH_SIZE?CORE_BATCH_SIZE:1;
 struct Pending{std::string_view sv,tv;char text[256];uint16_t sl=0,tl=0;Node from=0,to=0;CoreTemplateModel::PreparedRequest prepared;};std::array<Pending,batch_capacity>pending;unsigned used=0;uint64_t staged=0;
 auto source_view=[&](const Pending&r){return CORE_ZERO_COPY_BATCH?r.sv:std::string_view(r.text,r.sl);};auto target_view=[&](const Pending&r){return CORE_ZERO_COPY_BATCH?r.tv:std::string_view(r.text+r.sl,r.tl);};
 auto flush_batch=[&](){if(CORE_PREPARED){for(unsigned i=0;i<used;++i)predictor.prefetch_source_mask(pending[i].from,pending[i].to);for(unsigned i=0;i<used;++i){auto&r=pending[i];predictor.prepare_request(graph,r.from,r.to,r.prepared);predictor.prefetch_prepared(r.prepared,false);}for(unsigned i=0;i<used;++i)predictor.prefetch_prepared(pending[i].prepared,true);}else{for(unsigned i=0;i<used;++i)predictor.prefetch_request(graph,pending[i].from,pending[i].to,false);for(unsigned i=0;i<used;++i)predictor.prefetch_request(graph,pending[i].from,pending[i].to,true);}for(unsigned i=0;i<used;++i){auto&r=pending[i];process(source_view(r),target_view(r),r.from,r.to,CORE_PREPARED?&r.prepared:nullptr);}used=0;};
 if(CORE_ZERO_COPY_BATCH)reader->set_before_refill([&](){if(used)flush_batch();});
 while(next_line()){auto text=strip(line);if(text.empty())continue;auto comma=text.find(',');if(comma==text.npos || text.find(',',comma+1)!=text.npos)throw std::runtime_error("Invalid request row");auto s=strip(text.substr(0,comma)),t=strip(text.substr(comma+1));Node from=parser.pin(s),to=parser.pin(t);
  if(CORE_RING_PIPELINE && (CORE_BATCH_SIZE>0) && s.size()+t.size()<=256){unsigned slot=staged%batch_capacity;if(staged>=CORE_BATCH_SIZE){auto&r=pending[slot];process({r.text,r.sl},{r.text+r.sl,r.tl},r.from,r.to);}auto&r=pending[slot];r.sl=s.size();r.tl=t.size();r.from=from;r.to=to;std::memcpy(r.text,s.data(),s.size());std::memcpy(r.text+r.sl,t.data(),t.size());predictor.prefetch_request(graph,from,to,false);if(staged>=CORE_BATCH_SIZE/2){auto&next=pending[(staged-CORE_BATCH_SIZE/2)%batch_capacity];predictor.prefetch_request(graph,next.from,next.to,true);}++staged;
  }else if(CORE_BATCH_SIZE && !CORE_RING_PIPELINE && s.size()+t.size()<=256){auto&r=pending[used++];r.sl=s.size();r.tl=t.size();r.from=from;r.to=to;if(CORE_ZERO_COPY_BATCH){r.sv=s;r.tv=t;}else{std::memcpy(r.text,s.data(),s.size());std::memcpy(r.text+r.sl,t.data(),t.size());}if(used==CORE_BATCH_SIZE)flush_batch();}else{if(CORE_RING_PIPELINE && staged){uint64_t start=staged>CORE_BATCH_SIZE?staged-CORE_BATCH_SIZE:0;for(uint64_t j=start;j<staged;++j){auto&r=pending[j%batch_capacity];process({r.text,r.sl},{r.text+r.sl,r.tl},r.from,r.to);}staged=0;}if(used)flush_batch();process(s,t,from,to);}
 }if(CORE_RING_PIPELINE && staged){uint64_t start=staged>CORE_BATCH_SIZE?staged-CORE_BATCH_SIZE:0;for(uint64_t j=start;j<staged;++j){auto&r=pending[j%batch_capacity];process({r.text,r.sl},{r.text+r.sl,r.tl},r.from,r.to);}}if(used)flush_batch();
 if(descriptors.is_open()){descriptors.flush();if(!descriptors)throw std::runtime_error("Descriptor output write failed");}if(writer)writer->finish();else out.flush();if((!reader && in.bad()) || (!writer && !out))throw std::runtime_error("CSV I/O failure");std::cerr<<"rows="<<rows<<" cpu_seconds="<<double(std::clock()-begin)/CLOCKS_PER_SEC<<" initialization_seconds="<<init<<" arch_sha256="<<archdata::HASH<<'\n';if(cache)std::cerr<<"cache_hits="<<cache->hits<<" cache_misses="<<cache->misses<<'\n';
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<'\n';return 1;}}
