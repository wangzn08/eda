.DEFAULT_GOAL := all
CXX = c++
CXXFLAGS = -std=c++17 -O3 -Wall -Wextra -Wpedantic
XZ_OBJECTS = build/xz/xz_crc32.o build/xz/xz_dec_lzma2.o build/xz/xz_dec_stream.o

build/xz/%.o: src/vendor/xz/%.c src/vendor/xz/xz.h src/vendor/xz/xz_config.h src/vendor/xz/xz_private.h src/vendor/xz/xz_stream.h src/vendor/xz/xz_lzma2.h
	mkdir -p build/xz
	$(CC) -std=c99 -O3 -Isrc/vendor/xz -c $< -o $@

ARCH = data/EDA-PANGO-SRB-Arch-Delay/arch

.PHONY: all audit check refresh-architecture
all: build/estimate

refresh-architecture:
	python3 scripts/generate_architecture.py --arch "$(ARCH)" --out src/architecture_data.hpp

build/estimate: src/estimate.cpp src/architecture_data.hpp src/lookup_model.hpp src/spatial_model.hpp src/port_model.hpp src/source_x_model.hpp src/target_x_model.hpp src/dx_model.hpp src/route_v3_model.hpp src/forced_route_model.hpp src/route_v3_final_model.hpp src/v4_tree_model.hpp src/v4_table_model.hpp src/v4_horizontal_model.hpp src/v5_geometry_model.hpp src/v6_pair_model.hpp src/v7_tree_model.hpp src/v9_tree_model.hpp src/v10_tree_model.hpp src/v14_tree_model.hpp src/v19_tree_model.hpp src/local_path_oracle.hpp src/cycle_path_oracle.hpp src/cycle_prefix_bank.hpp src/macro_path_oracle.hpp src/repeat_cycle_jump.hpp src/phase_route_model.hpp src/phase_lower_bound.hpp src/routing_search.hpp src/potential_lower_model.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/estimate.cpp -o $@

audit:
	python3 scripts/audit_data.py

check: build/estimate
	python3 -m unittest discover -s tests -v
	python3 scripts/verify_baseline.py

# Architecture research utility; all returned bounds have path witnesses.
build/macro_oracle_apply: src/phase_lower_bound.hpp src/cycle_path_oracle.hpp src/macro_oracle_apply.cpp src/macro_path_oracle.hpp src/repeat_cycle_jump.hpp src/potential_lower_model.hpp src/cycle_path_oracle.hpp src/local_path_oracle.hpp src/cycle_prefix_bank.hpp src/architecture_data.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/macro_oracle_apply.cpp -o $@

# Periodic relaxed-graph assets. No request or golden data are used.
build/build_phase_bounds: src/build_phase_bounds.cpp src/architecture_data.hpp src/potential_lower_model.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/build_phase_bounds.cpp -o $@

build/compress_phase_bounds: src/compress_phase_bounds.cpp src/architecture_data.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/compress_phase_bounds.cpp -o $@

build/phase_estimate: src/repeat_cycle_jump.hpp src/phase_estimate.cpp src/routing_search.hpp src/phase_lower_bound.hpp src/cycle_path_oracle.hpp src/cycle_prefix_bank.hpp src/local_path_oracle.hpp src/potential_lower_model.hpp src/architecture_data.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/phase_estimate.cpp -o $@

# Direct periodic relaxation; experimental, no per-request graph search.
build/core_template_estimate: $(XZ_OBJECTS) src/xz_decode.hpp src/vertical_transient_model.hpp src/core_template_estimate.cpp src/core_template_model.hpp src/fast_residual_model.hpp src/fast_architecture_features.hpp src/routing_search.hpp src/architecture_data.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -ffp-contract=off -Isrc src/core_template_estimate.cpp $(XZ_OBJECTS) -lz -o $@

build/phase_fast_estimate: src/phase_fast_estimate.cpp src/fast_residual_model.hpp src/fast_architecture_features.hpp src/tiny_route_model.hpp src/periodic_dense_model.hpp src/phase_required_bound.hpp src/routing_search.hpp src/phase_lower_bound.hpp src/architecture_data.hpp src/potential_lower_model.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -ffp-contract=off -Isrc src/phase_fast_estimate.cpp -o $@

build/build_phase_required: src/build_phase_required.cpp src/architecture_data.hpp src/potential_lower_model.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/build_phase_required.cpp -o $@

build/build_periodic_anchor: src/build_periodic_anchor.cpp src/architecture_data.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/build_periodic_anchor.cpp -o $@

build/build_periodic_dense: src/build_periodic_dense.cpp src/architecture_data.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/build_periodic_dense.cpp -o $@

build/build_periodic_conditioned: src/build_periodic_conditioned.cpp src/architecture_data.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/build_periodic_conditioned.cpp -o $@

build/compress_periodic_dense: src/compress_periodic_dense.cpp src/architecture_data.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Isrc src/compress_periodic_dense.cpp -o $@

# Small min-plus experts; output channels are contiguous for SIMD evaluation.
build/tiny_route_estimate: src/tiny_route_estimate.cpp src/tiny_route_model.hpp src/direct_phase_bound.hpp src/fast_architecture_features.hpp src/routing_search.hpp src/phase_lower_bound.hpp src/architecture_data.hpp src/potential_lower_model.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) -ffp-contract=fast -Isrc src/tiny_route_estimate.cpp -o $@
