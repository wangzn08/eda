# V89: explicit corridor geometry ablation

## Rule-derived issue
SRB_Gap defines blocks spanningx76..89 with alternating50-row y intervals. Horizontal wires skip these14columns, paying292ps once per block; normal horizontal span remains possible in the gaps. V88 takes min(nominal full dx, nominal dx reduced14+292) without requiring the full-dx alternative to visit a gap. When both endpoints of the local bound lie in the same blocked y interval, a no-cross-cost route must leave that interval vertically.

## Approximate candidate
Optional --corridor-geometry checks actual bound endpoints after any initial net. For such same-band crossings, replace the full-dx candidate with nominal estimates using signed vertical total excursion:
- bottom corridor: -abs(dy)-2*(min(sourcey,targety)-lower+1), whenlower>0;
- top corridor: +abs(dy)+2*(upper-max(sourcey,targety)+1), whenupper+1<height.
Keep the compresseddx+292 candidate. Other requests keep original behavior. These excursions reflect geometric travel length, but feeding total vertical displacement into a single nominal template does not enforce actual port-compatible two-leg paths. Therefore this is an approximation ablation, not a legal-route certificate or lower/upper bound proof. It adds no asset and defaults off.

## Learning and evidence
Refit CatBoost signed residual on development against this changed baseline, same71features. Full150,053 validation and Python/C++ parity for64/128/256prefixes in V89-corridor-correction.json. No holdout. V88 reference scores98.9167/98.9380/98.9592. Conditional error diagnosis previously found crossing requests36.7% ofrows and55.4% oftotal score loss, but that alone did not prove this geometry fix would help. If score worsens, reject it and pursue port-aware corridor entry/exit composition.

## Reference boundary
Architecture-specific FPGA lookahead (Petelin/BetzFPL2016) provides general motivation; transit-node/entry-exit decomposition (Arz/Luxen/Sanders2013) motivates future port-aware candidates. Sources are listed in papers/README.md. Neither source validates this approximate displacement surrogate or establishes originality. The rule comes directly from official architecture JSON and Graph::move.

## Reproduce
make build/core_template_estimate
out/research-env/bin/python scripts/experiment_corridor_correction.py

No acceptance, full-billion timing or99.9 claim. Old frozen profiles and optionaloff behavior retained.

## Accuracy outcome
Architecture baseline98.9377260750 versusV88's98.5615496824 (+0.37618).64/128/256trees score99.0017779781/99.0145419745/99.0297139553, Python/C++ mismatcheszero for all150,053 rows. Onlydevelopment fits weights, holdoutunused. Improvement overmatchingV88 is0.08507/0.07656/0.07055. The geometry improvement reduces residual correction headroom but remains approximate.

64tree shorty group score98.77018 versus98.22439 previously; crossing98.55710 versus98.36564. Crossing still contributes0.53006 ofoverall0.99822 scoreloss (53.1%). Noncrossing99.25999, bothlong98.89591, shortxlongy99.21988; overlappinggroups. Remaining error needs port-compatible crossing paths and horizontal/vertical interaction investigation, not only more trees. Highest99.0297 still below99.9.

## Throughput outcome
64tree widefull-validation byte-exact withscalar. Actual10m totalCPU42.1372s/init5.73505s/query36.40215s,274,709.05 requests/CPU-second,maximumRSS1,339,883,520 bytes,runtimefiles95,948,632 bytes. ComparedwithV88query36.07949s,0.89%slower inthese single runs; precision99.00178versus98.91670. No one-hour margin and no99.9.256tree99.02971 wasnotthroughputbenchmarked. Candidate remainsoptional; allmeasurementjobscompleted, nofullbillionrun.
