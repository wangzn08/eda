# V82: coupled transient baseline and signed residual

## Motivation and references
The V79 vertical-only residual cannot be reused unchanged after adding horizontal transients: its training target changes. V82 fits the signed remaining delay error on development requests only, with the same 71 architecture features and y modulo 100 phase features. CatBoost (NeurIPS 2018, papers/README.md) is the existing learner, not an originality claim. FPGA routing lookahead (Petelin and Betz, FPL 2016) motivates topology-sensitive finite-distance models; our horizontal/vertical transient construction is an experimental extension, not a physical path certificate.

## Accuracy evidence
Full validation contains 150,053 requests. No holdout data is read. Architecture-only baseline scores 98.2499178531. New 64/128/256 tree models score 98.6185226889 / 98.6406738852 / 98.6700169907. Python and C++ predictions match for every candidate. Previous retained V79 best was 98.4920881081. The accuracy target 99.9 remains unmet. Validation has been used repeatedly for research selection, so these figures are not hidden-test guarantees.

## Optional joint RAM layout
For displacement in both long-distance axes, initialization precombines the core cost and the two transient corrections at period counts one and two. Four signed int32 bases and two nonnegative int32 growth slopes are stored for each source/target and signed anchor pair (160*160*20*24 entries, 294,912,000 bytes). Query growth cap and terminal-arc addition retain their original semantics. Short or single-long-axis requests keep the old computation. CLI --joint-layout is optional and defaults off. This caches architecture-derived coefficients, not request results. It adds no asset file. Full validation with the 128-tree residual is byte-identical to the original layout, with observed maximum RSS 929,267,712 bytes.

## Next architecture decision
Adding 128 more trees yields only 0.02934 points. New basis functions should describe finite-distance route switching rather than merely increasing tree count. Candidate investigations: extra measured distance bands, sparse breakpoints, and competing entry/repetition/exit route costs. Min-plus algebraic low-rank approximation (Hook 2017, papers/README.md) supports route-minimum decompositions; neither the method family nor minimum-over-routes is claimed as original. Any new basis must be checked against independent geometric distance bands before full validation and throughput comparisons.

## Reproduction
- out/research-env/bin/python scripts/experiment_coupled_correction.py
- make build/core_template_estimate
- out/research-env/bin/python scripts/benchmark_coupled_correction.py

Detailed actual 10-million-row measurements are in V82-coupled-throughput.json. Every request is computed, request cache disabled. These measurements do not establish official Linux compatibility or full-billion compliance. Frozen V79/V80/V81 profiles remain available.

## Measured throughput outcome
128-tree model, 10,000,000 repeated development requests, single runs: original layout total CPU 48.6289s, initialization 4.39552s, query 44.23338s, 226,073.61 requests/CPU-second. Joint layout total CPU 39.9805s, initialization 4.82459s, query 35.15591s, 284,447.20 requests/CPU-second. Query CPU decreased 20.52%; maximum RSS increased from 636,338,176 to 931,282,944 bytes. Runtime assets plus executable total 85,685,772 bytes. 256-tree accuracy result was not throughput-benchmarked; do not combine its 98.6700 score with the 128-tree timing. Optional layout remains default off pending broader displacement/parity coverage and repeated measurements.
