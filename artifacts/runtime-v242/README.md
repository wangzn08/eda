# V242 local joint-goal release

This folder contains the complete native program, its five required model/data assets, the liblzma license, and the exact runtime source closure. The prebuilt executable targets Apple M4/macOS ARM64. Source builds require a C++17 compiler, liblzma headers/library and zlib; a Linux build is supported by the Makefile but has not been performance validated here.

Run in this folder:

```sh
./estimate -in /absolute/path/request.csv -out /absolute/path/result.csv
```

Input header: `From,To`. Output header: `From,To,delay`.

To rebuild on the same Mac: `make rebuild`. On Linux: `make rebuild CXX=g++ ARCHFLAGS= LZMA_CFLAGS= LZMA_LIBS=-llzma`.

The program generates its short-distance field and terminal interval certificates from architecture kernels at initialization. Runtime reads neither original architecture JSON nor request answers. A development-trained shallow gate selectively runs the residual model. A bounded cache reuses intermediate architecture min-plus operators by relative geometry, core, terminal, legality and wall modes. It does not store absolute pin pairs, golden answers, line/source fees or final corrected predictions. Cache and candidate state are recreated in each process.

The local time target is measured using ten million repeated development request rows (700,705 distinct pin pairs), then extrapolated to one billion with one initialization. This throughput depends on intermediate-operator reuse and is not a guarantee for unseen inputs with little reuse, nor an official Linux result. Full fixed validation uses150,053 rows. Scores are the competition error score, not the percentage of exact predictions. Full validation score:99.5061105063. Two serial10m CPU runs extrapolate to536.2104/534.0712 seconds per billion, including initialization and CSV. Peak RSS:1,928,036,352 bytes. The complete folder including source is about96.62MB. These meet the agreed local repeated-input99.5/600s/100MB/2GB joint goal. Final measurements and integrity checks are tracked in reports/V242-joint-goal-profile.json and reports/V242-joint-goal-audit.json in the repository.

`BUILD_MANIFEST.json` records runtime and source hashes. Keep all five `.bin` assets beside `estimate`.

The standalone source rebuild was checked: all file-backed Mach-O sections are identical, with differences only in the link UUID and code signature. The included executable is the exact one used for the measurements.
