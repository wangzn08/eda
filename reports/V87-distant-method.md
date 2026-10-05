# V87: independently probe recurrence at96..119

## Question and reference
V84/V86 use measured vertical72..83 and84..95 to extend all greater distances. Compare that slope with independent architecture Dijkstra at96..107 and108..119. This follows the topology-sensitive lookahead motivation of Petelin/BetzFPL2016 and competing route costs in min-plus methods (Hook2017), recorded in papers/README.md. It is not a claim of a new shortest-path theorem.

## Setup
All160 source arrival ports and160 targets,59 signed x anchors, both y directions,12 residues. Nominal search domain[-144,144]^2 with cost limit5000. Original24..35 finite distances are subtracted together with125/127 base period prices. No golden development, validation or holdout labels enter generation. Finite domain effects remain possible; these are not physical route certificates.

## Storage
The replacement patch stores discrepancy from the original near extrapolation at period counts6,7. TRVFD002 header is magic8/hash64/ports320/transformuint32/decodedbytesuint64/firstperioduint32, thenXZ. It is distinct from V83 TRVFD001 (firstperiod4 implicit), and is not loaded by the current runtime. Exact lossless compression roundtrip is checked. Replacing existing far patch is considered, rather than adding another whole decoded table and exceeding file budget. Full validation and throughput for a matching generalized runtime are still required.

## Evidence
V87-distant-vertical-diagnosis.json compares near and current far extrapolations against the independently measured two distant bands, including absolute-error means/p95 and slope changes. These geometric errors are not validation scores. Current retained highest fast validation remains98.9243460840;64tree wide version98.8761669159 has actual10m queryCPU34.78726s. The combined99.9/one-hour objective is unresolved.

## Reproduction
c++ -std=c++17 -O3 -Isrc src/build_distant_vertical_transients.cpp -o build/build_distant_vertical_transients
build/build_distant_vertical_transients out/architecture-benchmark/periodic-dense.raw.bin out/architecture-benchmark/vertical-distant.raw.bin
out/research-env/bin/python scripts/analyze_distant_vertical_transients.py

## Findings and next decision
Current far model at96..107/108..119 has mean absolute residual error south0.23076/0.66667ps, north0.07658/0.21767ps, versus near-only south4.10941/5.52024ps, north1.80746/2.37309ps. Far slope changes in8.2938% of entries. Thus remaining geometric drift is smaller than before and may not account for the full validation gap.

Replacement patch XZ3 is14,904,576 bytes and yields100,061,564 total bytes with64trees, slightly over100MB. XZ6 reduces patch to10,775,132 bytes and total95,932,120, with exact decoded equality; compression33.50CPU seconds is offline only. A third-band incremental patch from the existing far model has6.93946% nonzero entries but compressed5,505,712 bytes, resulting103,118,524 total, so reject straightforward addition under current budget. Next candidate is replacing the two far anchor bands with96/108, generalized interpolation fromq2 toq6, and separately fitting its residual. Need full validation to determine whether worse intermediate-distance interpolation outweighs improved far slope. Existing runtime and retained prediction files are unchanged by this diagnostic.
