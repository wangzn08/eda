# V86: cover short-horizontal long-vertical queries

## Motivation and implementation
V85 compact joint layout covers only requests with both displacement axes long. This leaves requests with horizontal period countzero and positive vertical period count reading separate core and vertical near/far tables. Optional --wide-joint enables the V85 joint layout plus a separate10-byte architecture record for each source/target port, all59 signed x anchors and24 signed y anchors. The record holds four uint16 bases at verticalq1,q2,q4,q5 and one uint16 far growth slope. Horizontal correction iszero in this branch, as in the scalar predictor. q3 uses signed division after subtracting integer bases, preserving truncation towardzero. Every coefficient is range-checked at initialization. Extra memory362,496,000 bytes; no new disk assets or request-result cache.

## Numerical and throughput scope
scripts/benchmark_wide_piecewise.py first verifies byte-exact full validation output against V84 trees128, then computes10m repeated development requests with request caching disabled. It uses a128tree residual whose validation score is98.8964609173. Reports V86-wide-parity.json and V86-wide-throughput.json contain actual evidence. Measurements do not establish full-billion/hidden-workload or officialLinux performance. Highest separate256tree accuracy remains98.9243461, not the score of this speed candidate. Existing frozenV85 and earlier profiles are preserved; defaults remain unchanged.

## Research context
This layout experiment supports multi-band architecture transients motivated by FPGA lookahead (Petelin/Betz2016) and route-cost switching (Hook2017), documented in papers/README.md. Precombining coefficients is an engineering optimization, not a new shortest-path theorem or originality claim. The99.9 and one-hour objective remains active.

## Reproduction
make build/core_template_estimate
out/research-env/bin/python scripts/benchmark_wide_piecewise.py

##128-tree measured outcome
Full-validation byte-exact. Actual10m requests totalCPU43.8587s, initialization5.62646s, query38.23224s,261,559.35 requests/CPU-second. MaximumRSS1,340,522,496 bytes and runtimefiles98,142,476 bytes. Compared with V85 research query47.10097s, querytime decreases18.83%; compared with V84 query50.49961s,24.29%. Average throughput still below277,777.78 queries/CPU-second. Extra tree-budget candidates are measured by scripts/benchmark_wide_tree_budget.py, which verifies full validation parity independently for each prefix before throughput. Do not combine different prefixes' scores and times.

##64-tree measured outcome
Full-validation byte-exact with score98.8761669159. Actual10m totalCPU40.4107s/init5.62344s/query34.78726s,287,461.56 requests/CPU-second, RSS1,339,932,672 bytes, files97,612,812 bytes. This exceeds the one-hour implied average throughput on this repeated development mix, with each request computed and cache disabled; it does not prove the full goal or hidden performance. Precision is below99.9. Keep128/256 accuracy and their own throughput separate.

##256-tree measured outcome
Full-validation byte-exact, score98.9243460840. Actual10m totalCPU51.0559s/init5.74843s/query45.30747s,220,714.16 requests/CPU-second, RSS1,341,636,608 bytes, files99,201,804 bytes. Thus highest accuracy still lacks speed, and64trees has only98.8762 accuracy. No candidate meets the combined target. All jobs terminal, no full billion launched.
