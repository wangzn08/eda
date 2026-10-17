# Tight periodic and critical-cycle architecture experiments

Target: same standard-entry version validation>=99.5, extrapolated billion CPU<=600 sec, <=100MB submission and <=2GB RSS. Not achieved. Frozen V116 retained unchanged.

## Architecture-only direction bounds

V127 audits the 160-input folded graph (2752 edges). Its feasible two-dimensional potential polygon has four corners x=±12.5, y=+127/12 or −125/12. North and south optimal cycle costs differ. Integer scale12 allows exact Johnson reweighting and periodic reverse Dijkstra (10×12 residues). Six critical self-loop cycles support the four axis directions.

An unconstrained periodic relaxation omits mandatory access to long-cycle ports. All six full-validation cases finished; highest score94.54637923 with near finite hints and original-style corridor handling. Raw table304,742,848 bytes exceeds submission size. Screening query times do not establish billion throughput.

V128 augments phase states with two visited-critical-cycle flags. Each slope requires its own horizontal/vertical zero-cost self-loop families. Full validation8 cases completed, best95.63851187 at thresholds70/120 with corridor handling. RSS about1.073GB. Raw table609,485,248 bytes exceeds100MB. These are conditional path-family approximations, not feasible physical-path certificates. No labels used to build either table, no holdout read.

V130 tests selecting the slope matching displacement direction, rather than maximizing differently restricted cycle families. All eight cases completed; best95.55960109, below V128. Label-dependent oracle across baseline and all phase candidates99.30225220 is a diagnostic ceiling, not a predictor. V129 completed symmetric residual trees fitted only on development intrinsic diagnostics. Best99.17389131 (depth10,600 trees), below V125. Native deployment not selected.

## References and originality boundaries

Periodic state abstraction follows existing pattern database methods (Culberson/Schaeffer1998 and Felner et al.2004). Tight direction potentials and min-plus decomposition are established mathematical tools; FPGA graph-specific cycle access constraints and directional table composition are exploratory adaptations. Architecture-derived polygon audit is evidence, not an accuracy guarantee or claim of mathematical invention. Existing papers and bibliographic notes are in papers/README.md.

V131 ports the V125 residual to exact-double numeric C++ trees. Full150053 validation parity holds (99.21014442); packed model about3.1MB could fit with the existing lossless core asset compression. However model-only inference takes7.35525 CPU sec for3×150053 precomputed-feature rows, extrapolating about16340sec/billion before base estimation or CSV. Concurrent training was running, so this is screening only. Full-query deployment rejected; fitting a higher-score model alone does not satisfy the joint target. Details V131-intrinsic-native-probe.json.

## Next architecture decision

Avoid adding full-query deep tree ensembles: their native model-only cost exceeds the complete budget by a large margin. Next research should either build a compact correction representation evaluated in a few lookups, or identify a small difficult subset from architecture-derived quality indicators and run expensive correction there. Selection must use development labels, with full validation and whole-program CPU measurement; an oracle gate is not a deployable solution. Since phase candidate oracle is below99.5, phase-family selection alone cannot satisfy the precision target.

Training completed for all candidates. V129 best99.17389131. V131 isolated repeat after training:6.17863 CPU seconds per3×150053 rows (model-only precomputed features), about13,725sec per billion, still far above600sec. The earlier concurrent measurement7.35525sec is retained as a separate screening observation. This remains neither a whole-program benchmark nor a submitted version. All work in this wave completed; joint target remains unachieved.
