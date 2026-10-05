# V83: diagnose finite-distance route switching

## Question
V82 extends long distances using the increment measured between vertical bands36..47 and48..59. Does this increment remain appropriate at72..95? Answer using the nominal architecture graph rather than fitting request labels.

## Independent calculation
build_far_vertical_transients.cpp repeats nominal Dijkstra for all160 source arrival ports and160 target arrival ports. Displacement domain is[-112,112]^2, costs below4096. For each x anchor[-29,29], direction and residue0..11, save distances at72+residue and84+residue after subtracting original24+residue baseline and the usual125/127 periodic cost. Output has a distinct raw magic TRANSVF1 and compressed magic TRVFX001, preventing accidental loading through the ordinary near-transient loader. Finite graph distances may include domain-boundary effects and are not certified physical routes.

The analysis compares these independently calculated values to the previous growth extrapolation b+(q-2)*max(0,b-a), atq4 andq5. Far slope is compared with near slope. No development, validation or holdout labels enter asset generation. Exact XZ roundtrip is checked.

## Validation diagnostic
Separately, V82 trees128 errors are partitioned by geometric distance on the full validation set. Vertical separation>=144 contains80,752 of150,053 rows and contributes0.69769 of the overall1.35933 score loss. Long requests dominate total loss because there are many; short requests have worse average score. Thus distance-band improvement is plausible, not proved sufficient to reach99.9.

## Reference and originality boundary
Petelin and Betz, FPL2016 routing lookahead, motivates wire-topology-dependent delay tables. Hook2017 min-plus approximation motivates competing route costs. Both are recorded in papers/README.md. The next candidate is a piecewise finite-distance transient whose slope changes at measured bands, with sparse or compressed storage. This is an experimental combination of established ideas, not a claim of first publication.

## Reproduction
c++ -std=c++17 -O3 -Isrc src/build_far_vertical_transients.cpp -o build/build_far_vertical_transients
build/build_far_vertical_transients out/architecture-benchmark/periodic-dense.raw.bin out/architecture-benchmark/vertical-far.raw.bin
out/research-env/bin/python scripts/analyze_far_vertical_transients.py
out/research-env/bin/python scripts/analyze_coupled_errors.py

Read V83-far-vertical-diagnosis.json for measured recurrence errors and storage feasibility. This diagnostic does not change the retained predictor or establish validation improvement. Goal remains active.

## Outcome
22.9449% of architecture combinations change nonnegative growth slope. Existing near-band extrapolation at84..95 has mean absolute error2.841ps south/1.293ps north, with95th-percentile errors17/8ps. These are nominal architecture residual errors, not validation score gains. Full far asset20,334,184 bytes would exceed100MB with V82. Losslessly encoding only differences from the old extrapolation reduces it to12,455,824 bytes; V82 trees128 files plus patch total98,141,596 bytes, before any binary growth. Distinct TRVFD001 magic prevents loading as the original transient format. This establishes storage feasibility for a new piecewise candidate, not its accuracy or speed. Runtime integration, new matching residual training, and actual throughput are still required.
