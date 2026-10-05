# V88: replace far bands with96/108 and evaluate

## Architecture
Generalize VerticalTransientModel to first_far_period4 (TRVFD001) or6 (TRVFD002). Header2 explicitly carries firstperiod6, checked before exact XZ decode. Preserve nearq1/q2. For2<q<firstperiod interpolate signed correction as b+(far-b)*(q-2)/(firstperiod-2), with signed division towardzero. Firstperiod exact, then final band's correction plus nonnegative measured increment for later distances. Both compact and wide precombined layouts use the same period metadata and formulas, so the existing q4/q5 architecture remains supported.

Replacement patch V87 XZ6 has10,775,132 bytes, allowing disk budget without adding a third table. No request labels enter these architecture coefficients. Nominal finite graph behavior remains approximate and is not a physical route certificate.

## Learning and measurements
Fit separate signed CatBoost residual only on development with original71features and obstacle phases. Prefixes64/128/256 receive full150,053 validation, Python/C++ exact parity, and separate results in V88-distant-correction.json. Wide layouts are compared against scalar output before actual10m measurement by benchmark_distant_correction.py. No holdout and no result caching. Reference V86 scores64:98.8761669,128:98.8964609,256:98.9243461. Later anchors may degrade medium-distance interpolation, so do not assume improvement from more distant measurements.

## References
FPGA topology-sensitive lookahead (Petelin/BetzFPL2016) and route-cost switching/min-plus modeling (Hook2017), papers/README.md. Changing measured distance bands and factoring coefficients are experimental adaptations, not claims that the reference algorithms or boosting were invented here.

## Commands
make build/core_template_estimate
out/research-env/bin/python scripts/experiment_distant_correction.py
out/research-env/bin/python scripts/benchmark_distant_correction.py

Goal99.9 and single-thread one-hour billion remains active. No full-billion, hidden workload, or officialLinux compliance is established by these research runs.

## Accuracy outcome
Baseline98.5615496824 versus previous98.5154851356. New64/128/256 full-validation scores98.9167049081/98.9379786268/98.9591603250, all Python/C++ prediction mismatcheszero. Compared with matchingV84/V86 prefixes, gains0.04054/0.04152/0.03481 points. This is a modest positive result, not sufficient to reach99.9; merely moving distance bands further may have diminishing returns. Preserve previous profiles and score/time pairing.

## Remaining-error diagnosis
V88trees64 full validation: block-crossing55,123 rows score98.36564, contributes0.60039 oftotal1.08330 score loss; noncrossing94,930 rows score99.23669 contributes0.48290. Crossing uses current approximate14-column/292ps shortcut, not a certified detour. It accounts for55.4% of score loss despite36.7% of requests. Shorty18,684 rows score98.22439 contributes0.22109; these groups overlap. Next investigate topology-dependent crossing entry/exit costs and legal corridor candidates, rather than only extending vertical anchors again. These statistics are research diagnostics on reused validation, not proof of causality or hidden accuracy.

## Actual throughput and compatibility
64trees:10m totalCPU41.8271s/init5.74761s/query36.07949s,277,165.78 requests/CPU-second, maxRSS1,339,932,672 bytes,files95,932,120.128trees: total45.3202s/init5.77265s/query39.54755s,252,860.16/s,RSS1,340,473,344,files96,461,784. Both wide outputs byte-identical to scalar full validation.64throughput is slightly below the one-hour implied average, with no robust margin. Do not present256tree98.9592 with64tree timing. Generalized runtime also preserves full150,053 originalfirstperiod4 wide64 predictions byte-exact. No combined-goal success claim.
