CXX = c++
CXXFLAGS = -std=c++17 -O3 -Wall -Wextra -Wpedantic
ARCH = data/EDA-PANGO-SRB-Arch-Delay/arch

.PHONY: all audit check refresh-architecture
all: build/estimate

refresh-architecture:
	python3 scripts/generate_architecture.py --arch "$(ARCH)" --out src/architecture_data.hpp

build/estimate: src/estimate.cpp src/architecture_data.hpp src/lookup_model.hpp src/spatial_model.hpp src/port_model.hpp src/source_x_model.hpp src/target_x_model.hpp src/dx_model.hpp src/route_v3_model.hpp src/forced_route_model.hpp src/route_v3_final_model.hpp src/v4_tree_model.hpp src/v4_table_model.hpp src/v4_horizontal_model.hpp src/v5_geometry_model.hpp src/v6_pair_model.hpp src/v7_tree_model.hpp src/v9_tree_model.hpp src/v10_tree_model.hpp src/v14_tree_model.hpp src/local_path_oracle.hpp src/cycle_path_oracle.hpp src/cycle_prefix_bank.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/estimate.cpp -o $@

audit:
	python3 scripts/audit_data.py

check: build/estimate
	python3 -m unittest discover -s tests -v
	python3 scripts/verify_baseline.py
