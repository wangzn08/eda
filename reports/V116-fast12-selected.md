# V113–V116 architecture comparison and selected profile

Selected: **V116**, compact coefficients, phase-major records, packed near indices, staged16 prefetch, shared within-request corridor legs, source8 and terminal1 candidates. Standard entry: `out/phase-fast12-v116/estimate -in requests.csv -out predictions.csv`.

| Profile | Validation score | Billion CPU estimate, seconds (two10m runs) | Peak RSS bytes |
|---|---:|---:|---:|
| V115 | 99.0256649430 | 693.2576 / 695.1289 | 1,624,686,592 |
| V116 | 99.0256649430 | 684.0975 / 689.4150 | 1,624,555,520 |

Both pass the local12-minute target with all validation and10m outputs identical to V112. V116 is the faster candidate on both measured rounds. Runtime assets plus executable are99,293,176 bytes; full directory remains below100MB. All five asset and executable hashes verified. No request prediction cache; no holdout used. Previous V112 preserved.

Compared: scalar fusion, batches16/32/64, packed near indices, adaptive source4/8, ring software pipeline, core phase permutation, corridor leg sharing, logical-target fusion and coefficient compaction. Ring did not beat batching. Logical-target fusion exceeded2GB; after compaction still2,008,481,792 bytes and rejected. Adaptive pruning met score99 but changed validation predictions; selected profile avoids that loss. The frozen candidates remove redundant coefficients without changing existing search predictions.

Actual measurement is two serial10m repeated development requests, including CSV I/O. Billion estimates count initialization once. Apple M4/macOS, single thread. Not an actual billion run, official Linux benchmark, hidden-test accuracy guarantee, or evidence of first place. Official scoring validation score is not an exact-match percentage.

Reference: Kocberber et al., Asynchronous Memory Access Chaining, PVLDB9(4),2015, https://www.vldb.org/pvldb/vol9/p252-kocberber.pdf . Staged prefetch is inspired by latency hiding; this is not a full AMAC reproduction. Compaction exploits exact algebraic relationships in the estimator records.

Next research should compare independent per-request candidate staging against fixed batches, examine the tail of validation errors using structural route families, and measure the selected entry on the official Linux environment. Hidden data must stay unused for fitting. A first-place claim requires official leaderboard evidence.
