# V250 score-oriented runtime

Standard entry: `./estimate -in requests.csv -out predictions.csv`.
Input header: `From,To`; output: `From,To,delay`.

The prebuilt executable is Apple M4/macOS ARM64. Full validation score:
99.5290712686. The competition score is not an exact-match percentage.
Two serial runs use disjoint synthetic, nonrepeated requests newly recombined
from development pins. Their local single-thread CPU extrapolation to one
billion requests, including one initialization and CSV I/O, averages
1743.7680 seconds (29.0628 minutes). This is not an official
hidden-input or Linux result. Peak runtime RSS: 1923153920 bytes.

Physical short-distance/response kernels select the route. One development-trained numeric expert is selected by whether the chosen route crosses the vertical wall.
The model also uses integer endpoint/curve interaction features.
The intermediate operator cache is disabled; no final prediction cache or
golden answers are read. Gate enabled: True.

Keep estimate, all five .bin files and the liblzma license together.
The included source closure can be rebuilt with `make rebuild`; it needs a
C++17 compiler, zlib and liblzma. Python 3 standard library regenerates the forest header from correction.bin in a temporary directory; LightGBM and training data are not required.

On Linux: `make rebuild CXX=g++ ARCHFLAGS= LZMA_CFLAGS= LZMA_LIBS=-llzma`.
Linux performance has not been measured. Rebuilding can change the Mach-O UUID
and code signature; the distributed executable is the one actually measured.
