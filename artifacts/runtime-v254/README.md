# V254 score-oriented runtime

Standard entry: `./estimate -in requests.csv -out predictions.csv`.
Input header: `From,To`; output: `From,To,delay`.

The prebuilt executable is Apple M4/macOS ARM64. Full validation score:
99.5061105063. The competition score is not an exact-match percentage.
Two serial runs use disjoint synthetic, nonrepeated requests newly recombined
from development pins. Their local single-thread CPU extrapolation to one
billion requests, including one initialization and CSV I/O, averages
1262.8925 seconds (21.0482 minutes). This is not an official
hidden-input or Linux result. Peak runtime RSS: 1962016768 bytes.

Physical short-distance/response kernels select the route. The existing single residual forest and shallow gate are retained.
The model uses137 geometry, response and endpoint-potential features.
The intermediate operator cache is disabled; no final prediction cache or
golden answers are read. Gate enabled: True.

Keep estimate, all five .bin files and the liblzma license together.
The included source closure can be rebuilt with `make rebuild`; it needs a
C++17 compiler, zlib and liblzma. The exact generated forest header is included. No Python packages or training data are needed to rebuild.

On Linux: `make rebuild CXX=g++ ARCHFLAGS= LZMA_CFLAGS= LZMA_LIBS=-llzma`.
Linux performance has not been measured. Rebuilding can change the Mach-O UUID
and code signature; the distributed executable is the one actually measured.
