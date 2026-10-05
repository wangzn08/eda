# V84: piecewise finite-distance vertical transients

## Method and rationale
V83 independently measured nominal shortest distances at vertical bands72..83 and84..95. V84 retains near transient bands36..47 and48..59; for period countq3 it interpolates the correction betweenq2 andq4 using C++ signed integer division (truncation towardzero), q4 uses its measured value, and q>=5 uses measuredq5 plus(q-5)*max(0,f5-f4). Global125/127 periodic prices remain outside the correction. Existing horizontal transient correction is unchanged. This is an approximate nominal delay model, not a feasible physical path or bound certificate.

The extra asset stores int16 discrepancies against the old near-band extrapolation, with magicTRVFD001, hash/ports/transform/decoded-size checks and exact XZ stream consumption. Loader reconstructs far correction on demand. --far-vertical-delta requires a vertical asset and unlimited growth cap. CLI defaults preserve earlier models. Request cache remains disabled.

## Learned correction and validation
Only development labels fit CatBoost256depth10 MAE trees with relative-error sample weights. New residual target is(y-new_baseline)/100. Features71 and phase features match V82; no holdout is read. Full validation150,053 rows: baseline98.5154851 (V82 baseline98.2499179), trees64/128/256 scores98.8761669/98.8964609/98.9243461. All exported C++ predictions exactly match Python. Best V82 score98.6700170, so this architecture change improves the best candidate by0.25433 points. 99.9 remains unmet; repeated validation model selection is not independent hidden evidence.

## Query layout
Existing precombined near costs are retained. An optional additional FarJointCell stores four bases (x period count1/2 crossed with y4/5) and one nonnegative y slope for each signed anchor pair. Its allocation is245,760,000 bytes, in addition to the294,912,000-byte near layout and144,998,400-byte decoded far patch. Atq3, subtracting two bases cancels horizontal and core terms before signed interpolation, reproducing the scalar correction exactly. CLI --joint-layout enables it; default stays off. Full validation parity and actual10m measurements are recorded separately.

## Reference and innovation scope
Petelin and Betz FPL2016 motivates architecture-dependent lookahead; Hook2017 min-plus approximation motivates route-switching interpretations (papers/README.md). The measured multi-band transient, lossless discrepancy asset, and precombined query coefficients form an experimental engineering combination. These references do not establish that this combination is globally original. Neither tree boosting nor table compression itself is an invention claim.

## Reproduce
make build/core_template_estimate
out/research-env/bin/python scripts/experiment_piecewise_correction.py
out/research-env/bin/python scripts/benchmark_piecewise_correction.py

The256-tree accuracy must not be combined with128-tree throughput. Prior frozen profiles remain intact. No full-billion run, official Linux acceptance or final goal completion is claimed.

## Actual throughput result and rejection as speed replacement
Full joint/scalar validation output is byte-exact. Actual10m repeated development requests,128trees,no request cache: total CPU56.0568s, initialization5.55719s, queries50.49961s,198,021.33 requests/CPU-second; maximumRSS1,322,041,344 bytes. Runtime files98,142,076 bytes. Versus V82 joint128 query35.15591s, queries are43.64% slower despite better accuracy. This candidate is retained as a research accuracy improvement, not a replacement satisfying the time objective. Next investigate combining near/far coefficients into one cache-local record and compressing redundant piecewise coefficients; current two-array accesses and larger working set are plausible causes, not yet isolated by measurement.
