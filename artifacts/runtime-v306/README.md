# V306: novel-request 600 second budget

Run `./estimate -in requests.csv -out predictions.csv` with all .bin files
beside the executable. Input: `From,To`; output: `From,To,delay` in ps.
The supplied binary is for Apple M4 / macOS ARM64.

Full 150053-row native validation score: 99.1137582293.
This competition score is not the percentage of exactly correct answers.
Two disjoint 3000000-row novel request batches extrapolate to
488.596014 CPU seconds per billion, including one initialization and CSV.
Each measured batch must stay below 600 seconds for this release to freeze.
Peak RSS: 1711685632 bytes. One runtime thread was observed.
These are local synthetic novel-request extrapolations, not official judge
results or a guarantee about another computer or hidden request distribution.

Architecture: periodic finite min-plus responses, fixed-layout terminal
selection and corridor costs, plus out/v288/eight511.txt with 56 inexpensive raw
geometry and static port features. Training uses development labels only.
The physical estimates are approximate. No final prediction cache or
intermediate operator cache is used. No golden labels are runtime assets.

`make rebuild` uses the captured source, generated tree and port metadata,
and development-only LLVM PGO profile. Python standard library expands the
lossless generated architecture header in a temporary source directory.
LightGBM and training inputs are not needed to rebuild. Compiler, zlib and
liblzma are required. PGO profile was produced with Apple Clang 21.
Linux example: `make rebuild CXX=g++ ARCHFLAGS= LZMA_CFLAGS= LZMA_LIBS=-llzma PGO=0`.
Linux performance is unmeasured. The distributed binary is the measured one.
