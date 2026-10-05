# V91: diagnose directional interaction and build a joint correction

## Independent probe
Nominal Dijkstra on[-144,144]^2,limit5000; sources0,80,159, all160targets and allfour signs/residue pairs. Compare vertical-only displacementx20..29,y96..107, horizontal-onlyx70..79,y24..35, andjointx70..79,y96..107. No development/validation/holdout labels are read.691,200 totalcases. Probe matches current template + directionaltransients + distantq6/q7vertical model, excluding actual physical gaps/blocks and any learned residual.

## Finding
Vertical-only controls areall exact atmeasured anchor; horizontal-only meanabs errors1.48..3.51ps, whilebothlong5.29..11.90ps. P95joint errors28..47ps. Additionalerror beyondmatchedcontrols meanabs8.725ps,p9534ps. This supports directionalinteraction as a new candidate cause; it doesnot establish a unique causal decomposition or validation gain. Three-sourceprobe cannotstandforallports.

## All-port patch
RepeatDijkstra for all160sources, store signedint16 difference true_nominal - direct_pair_estimate atx70..79,y96..107, all160targets/four signs/10x12residues. Directpair excludes terminalincoming minimization, so a future patch must be applied percandidateprecursor beforeminimization. Raw24,576,000bytes, distinctTRJRAW01header. XZ3/6 variants include decodedlength, anchorperiods5/6 andbaseline-recipehash derivedfrom fourassetSHA256values. Tablecoupling depends onbaseline assets, notonly architecturehash. Compressionroundtripchecked. Assetformatsare notyetreadbyruntime.

## Next evaluation requirement
A distance-dependent interaction patch shouldbe tested atother distancebands; oneanchor cannotprove generalization. Needfit scaling fromarchitecture-only cases, thenrefitdevelopmentresidual,fullvalidationand actual10mthroughput. Currenthighestretainedfullvalidationscore99.0597877,combinedgoalunmet. Optionaldebugmethodsarenominalresearchaccessors,notpathcertificates.

## Reference and originality
Hook2017min-plus low-rank approximation motivatescoupledroutecosts; Petelin/Betz2016 FPGAlookahead motivatesfinite topology tables (papers/README.md). Additive directional costis anapproximation, andmin-plus/table ideasare priorwork. Jointarchitecture-deltacompression isanexperimental engineeringcombination,notclaimofglobaloriginality.

## Storage outcome
All160source patch XZ3=5,059,944bytes, exceedingcombinedbudget101,010,448. XZ6=3,861,388bytes, combinedV90trees64files99,811,892bytes beforefutureexecutablegrowth. Exactdecodedroundtrip; offlinecompression7.56CPU seconds. Budgetmarginonly188,108bytes, so verifyactualfuturestandalonefilemanifest ratherthanassuming compliance. No runtimevalidationgain is established. XZ6patch iscandidatefor distance-generalization probes and64tree matchingresidual;128/256tree filebudgets willrequireother savings.
