CXX = c++
CXXFLAGS = -std=c++17 -O3 -Wall -Wextra -Wpedantic
ARCH = data/EDA-PANGO-SRB-Arch-Delay/arch

.PHONY: all audit check refresh-architecture
all: build/estimate

refresh-architecture:
	python3 scripts/generate_architecture.py --arch "$(ARCH)" --out src/architecture_data.hpp

build/estimate: src/estimate.cpp src/architecture_data.hpp src/lookup_model.hpp src/spatial_model.hpp src/port_model.hpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) src/estimate.cpp -o $@

audit:
	python3 scripts/audit_data.py

check: build/estimate
	python3 -m unittest discover -s tests -v
	python3 scripts/verify_baseline.py
