# V94/V95: preserve predictions while reducing query work

## V94
Move request-displacement classification, signed-anchor indexes, source row offsets and interaction scaling weight outside the terminal predecessor loop. Interpolation divides explicitly by4 for firstperiod6 or2 for firstperiod4, preserving signed integer truncation and eliminating general integer division. Saturated interaction weight30 adds the exact delta directly. Numeric formulas and candidate-minimum order are retained. Full150,053validation byte-exact toV93trees64, score99.1667785525.

Actual10m repeateddevelopment/cacheoff totalCPU46.4666s,initialization5.8414s,query40.6252s,246,152.63requests/CPU-second,RSS1,389,068,288bytes,files99,812,292. PreviousV93query43.09563s:5.73%less inthese single runs, no final-billion or hidden-mix evidence.

## V95 candidate
Quantize only features referenced by loaded trees. Every split's feature is present in the active set. Prefix quantizers retain original rank mapping. For commondepth10, explicitly form all10leaf-index bits, avoiding loop iteration; otherdepths retain original loop. Double leaf accumulation remains original treeorder and ff-contractoff. No retraining, no new assets, no requestresultcache. Fullvalidation byte-parity must precede actual10m measurement in benchmark_unrolled_joint.py.

## Research scope
These are implementation optimizations supporting the topology/interaction architecture, not new learning or shortest-path algorithms. References/methodlimitations remain inV92-V93-joint-method.md. Target99.9 and one-hour single-thread billion still unmet. Current independent officialLinux acceptance and arbitrary hidden-query mix unverified.

## V95 measured outcome
Full150,053validation byte-exact toV93trees64, score99.1667785525. Actual10m repeateddevelopment/cacheoff totalCPU45.2302s/init5.76871s/query39.46149s,253,411.62requests/CPU-second,RSS1,389,051,904bytes,files99,812,516. ComparedV94query40.6252s,2.86%less; comparedV93query43.09563s,8.43%less. Allsingle-runmeasurements, no statistical repeatability claim. Retain numeric-preserving optimizations, but one-hour implied average277,777.78/s still higher and99.9 unmet. No resultcache or billion run. Alljobscompleted.
