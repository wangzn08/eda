# V90: port-compatible corridor composition pilot

## Candidate
For same-band block-crossing requests, replace the V89 single total-excursion nominal surrogate with a min-plus composition through arrival hubs at a real gap coordinate(cx82,cy lower-1 orupper+1). Candidate cost=nominal(sourceport,hub,cx-sourcex,cy-sourcey)+nominal(hub,targetport,targetx-cx,targety-cy). Both pieces share the same hubport. Include extra y line-gap crossings for vertical backtracking; monotone x line gaps are already added globally. Retain the reduced14-column candidate plus292ps. Other requests are unchanged.

Optional --corridor-hubs1..32 requires --corridor-geometry. Hubs are existing long-wire arrival ports, sorted deterministically by netdelay thenportid; full32covers long horizontal andvertical inputs. Defaults do not enable them. No additional disk asset. Each nominal segment is still approximate and may take an unconstrained interior route; sharing hubport is not proof of a feasible physical path. This method must not be advertised as a certified route or distance bound.

## Reference
Transit Node Routing Reconsidered (Arz/Luxen/Sanders2013), route cost via entry/exit transit nodes; Hook2017 min-plus approximation, composition of route minima; FPGA lookahead (Petelin/Betz2016). Local papers andlinks in papers/README.md. These established decomposition ideas are not claimed as original. Application to cheap nominal corridor estimates is an experiment, whose usefulness depends on measured accuracy and cost.

## Pilot scope
Fixed2048 evenly spaced validation rows with opposite-side crossing and endpoints in the same blocked50-row band.0/4/16/32hubs, no learned residual, no holdout or fitting. Baseline is the current scalar V89 architecture. Report score andqueryCPU after initialization; selection is intentionally targeted and not representative full validation. A larger score must precede refitting/full validation, and microbenchmarks do not prove billion throughput.

## Reproduction
make build/core_template_estimate
out/research-env/bin/python scripts/evaluate_corridor_hub_pilot.py

Retained highest fast full-validation remains99.0297139553 before this experiment. Goal99.9/one-hour remains active.

## Pilot outcome and selection
0/4/16/32hubs targetedpilot scores97.03501/98.55828/98.65434/98.78109. Meanabs errors13.6143/6.3901/5.9741/5.4834ps, queryCPU0.02654/0.03054/0.08492/0.16535s for2048rows. These are single shortpilot measurements with initialization subtracted, not reliable standalone throughput estimates.4hubs is selected for full-development fitting/full-validation evaluation because it captures most score gain at substantially lower measured query cost. Higherhub variants are not retained as speed candidates yet. Matching scriptsexperiment_corridor_hub_correction.py andbenchmark_corridor_hub_correction.py use exactly4hubs.

## Full validation outcome
Architecture baseline98.9705850537 versusV89's98.9377260750. Separatedevelopment-fit residual64/128/256 scores99.0211196777/99.0438423138/99.0597877269, withzeroPython/C++ mismatches acrossall150,053 validationrequests. ComparedwithmatchingV89 prefixes, gains0.01934/0.02930/0.03007. The targetedpilot improvement is not the full-validation gain; affectedsubset is small. Best99.0598 isstillbelow99.9. Matching64treewide throughput is evaluated separately; do not combine256scorewith64timing.

## Actual throughput outcome and decision
64treewide output byte-exact toscalarfullvalidation. Actual10m repeated development requests,cacheoff:totalCPU43.4114s/init5.7628s/query37.6486s,265,614.13requests/CPU-second,RSS1,339,883,520bytes,files95,950,504bytes. ComparedwithV89'squery36.40215s,thisis3.42%slower for0.01934pointsaccuracygain. Retainasoptionalresearcharchitecture, not a one-hour-target replacement. Largerhubcounts only have targetedpilot evidence. Next reduce candidate evaluations or explore interactions outside the same-band subset; merely adding more hubs is not justified by this tradeoff. Alljobscomplete,goal99.9/one-hourunmet.
