CXX = clang++
CXXFLAGS = -std=c++17 -O3 -Wall -Wextra -Wpedantic
ARCH = data/EDA-PANGO-SRB-Arch-Delay/arch
ARCH_FILES = $(wildcard $(ARCH)/SRB_*.json)

.PHONY: all audit check
all: build/estimate

build/architecture_data.hpp: $(ARCH_FILES) scripts/generate_architecture.py scripts/architecture.py
	python3 scripts/generate_architecture.py --arch "$(ARCH)" --out $@

build/estimate: src/estimate.cpp build/architecture_data.hpp
	$(CXX) $(CXXFLAGS) -Ibuild src/estimate.cpp -o $@

audit:
	python3 scripts/audit_data.py

check: build/estimate
	python3 -m unittest discover -s tests -v
	python3 scripts/verify_baseline.py
