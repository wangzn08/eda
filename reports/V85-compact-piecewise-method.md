# V85: lossless coefficient factoring for piecewise queries

## Change
V84 joint query reads both a24-byte near record and a20-byte far record. Four far bases repeat the same horizontal correction difference. V85 factors it out: one16-byte record contains four uint16 bases (verticalq1,q2,q4,q5, horizontalq1), one signed int16 horizontal delta, and three uint16 slopes. Initialization checks every coefficient for overflow. Whenxq>=2, add the signed horizontal delta plus(xq-2)*max(0,delta). Theq3 interpolation happens before horizontal addition, preserving signed truncation exactly. These transformations preserve V84's approximate predictor; they do not make it a physical route certificate.

Joint storage decreases540,672,000 to196,608,000 bytes. The original near-only V82 layout is retained when no far patch is loaded. Default research CLI layout remains off; the frozen V85 profile compiles default128trees and jointlayouton, auto-loads sibling vertical-far-delta.bin, and retains standard -in/-out interface. Prediction caching defaults off.

## Evidence and scope
Full150,053 validation outputs must be byte-identical to V84 trees128 (98.8964609173). See V85-joint-parity.json, V85-compact-throughput.json and V85-standalone-profile.json for actual measured evidence.256tree score98.9243461 is not attributable to the128tree speed measurement. Actual10m throughput computes every repeated development request; it is not final-billion, hidden-mix or official Linux proof. The99.9 goal remains unmet.

## References and novelty
This is algebraic coefficient factoring and cache-local data layout, not a claim of a new learning algorithm. It supports the multi-band architecture model motivated by FPGA lookahead (Petelin/Betz2016) and min-plus route costs (Hook2017), listed in papers/README.md. Numerical parity is necessary to distinguish a speed improvement from a changed approximation.

## Reproduction
make build/core_template_estimate
out/research-env/bin/python scripts/benchmark_compact_piecewise.py
out/research-env/bin/python scripts/prepare_v85_profile.py

## Measured outcome
Research binary128trees full-validation byte-exact. Actual10m query CPU47.10097s versusV84's50.49961s, a6.73% reduction; total52.4496s/init5.34863s, throughput212,309.85 requests/CPU-second. RSS977,911,808 bytes versus1,322,041,344 (344,129,536 bytes reduction). Runtime file bytes98,142,028. This remains below the277,777.78 queries/CPU-second implied by a one-hour billion average, and is not a speed-target solution. Frozen standard-interface profile total98,142,012 bytes and full-validation parity verified independently.

A remaining coverage gap is that precombined records are used only when both axes are long. Requests with shortx and longy still perform separate core/near/far/horizontal table reads. Extending joint coverage across all59 x anchors with explicit horizontal-entry coefficients is a next candidate within2GB; it must preserve zero horizontal correction atshortx and signed interpolation semantics. Merely extrapolating throughput is not an acceptance result.

Frozen standard-interface actual10m: totalCPU52.2472s, init5.30717s, query46.94003s,213,037.78 requests/CPU-second, maximumRSS977,895,424 bytes. This agrees with research throughput and confirms the unresolved speed gap.
