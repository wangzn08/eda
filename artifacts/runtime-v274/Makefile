CXX = clang++
CXXFLAGS = -O3 -std=c++17
ifeq ($(shell uname -s),Darwin)
ARCHFLAGS ?= -mcpu=apple-m4
LZMA_CFLAGS ?= -I/opt/homebrew/include
LZMA_LIBS ?= /opt/homebrew/lib/liblzma.a
else
ARCHFLAGS ?=
LZMA_CFLAGS ?=
LZMA_LIBS ?= -llzma
endif
.PHONY: rebuild
rebuild:
	python3 rebuild.py --cxx='$(CXX)' --cxxflags='$(CXXFLAGS)' --archflags='$(ARCHFLAGS)' --lzma-cflags='$(LZMA_CFLAGS)' --lzma-libs='$(LZMA_LIBS)'
