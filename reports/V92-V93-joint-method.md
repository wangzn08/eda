# V92/V93: distance-scaled joint directional correction

## Architecture-only selection
V92 evaluates qx{1,3,5,7},qy{2,4,6,8}, allfour signs/10x12residues, sources0/80/159 and160targets. Excludingpatchanchor(qx5,qy6) leaves3,456,000 nominal finite-graph cases. Meanabs error baseline6.48302ps; unscaledpatch4.96433; clippedminimumratio2.57090; clippedproduct2.70945; q1fade2.99999. Choose minimumratio by this geometric evidence, not goldenrequestlabels. Sourceswere includedinallportpreprocessing,so this ishelddistanceevidence,not unseenport evaluation or physicalpathcertification.

## Runtime
--joint-interaction loads TRJXZ001, checksarchitecturehash,ports, decodedbytes24,576,000, anchorperiods5/6, fixedbaseline-recipeidentifier, andexactXZstream consumption. Requiresdistantverticalfirstperiod6 andhorizontaltransient. Apply correctionperterminalprecursor beforeclamping andminimization, afteroriginal scalarorprecombined value:
 delta * min(min(qx,5)*6,min(qy,6)*5) /30
withsignedinteger divisiontowardzero. Zerowhen eitheraxisnotlong. Recipeidentifierbindsdeclaredgenerationrecipe; runtime doesnot computeSHA256ofthefourloadedbaselinefiles. Researchcommands use theexactrecordedassets; anyfinalprofile mustverifytheiractualhashes inpreparation/manifest. Defaultsleaveinteractionoff.

## Learning and budgets
Fitfreshsignedresidual ondevelopmentonly againstmodifiedbaseline,same71features. Fullvalidation150,053 andPython/C++parityfor64/128/256 inV93-joint-correction.json. XZ6patch3,861,388bytes means64treecandidate diskbudgetisverytight(~99.81MBbeforebinarychanges);128/256 mayexceed100MB andmustnotbe presentedasfeasible submissionswithoutactualmanifest. No holdout, no requestresultcache. Matchingwide64throughput measuredseparatelyafterfullscalarparity.

## References and limitations
Min-plusroutecosts(Hook2017) andFPGAlookahead(Petelin/Betz2016),papers/README.md. Additiveaxesignoredsharedentry/exit effects; measuredjointdeltas anddistance-scaledcompressionareengineeringhypotheses. Theydonotestablish globaloriginality or routecertificates. Current99.9/one-hourgoal remainsunproven.

## Validation outcome and fused layout
Baseline99.1158427847.64/128/256development-fitprefixesfullvalidation99.1667785525/99.1815380285/99.1963307706,Python/C++mismatcheszero. ComparedwithV90sameprefixes,gains0.14566/0.13770/0.13654.256scoreisresearch-onlyundercurrentfilebudget; do notdeclarelargertreeprofilesfeasiblesubmissions.

Jointdeltaisfusedintoeachlong-longprecombinedrecord,18bytesinsteadof16. Thisadds24,576,000bytesjointRAMwhile avoidingaseparatetablelookup. Scalarfallbackusestheoriginaldecodedpatch. Bothperformtheidenticalsignedscalingbeforefinalcandidateclamping/minimum. benchmark_joint_correction.py checks full150,053wide/scalarbyteparitybeforeactual10m64treerun. PreparationexperimentandbenchmarkalsoverifySHA256ofallfourbaselineassetsagainstgenerationprovenance,asruntimeonlychecksdeclaredrecipeidentifier.

##18-byte actual throughput
64treefullwide/scalarvalidationbyte-exact. Actual10m totalCPU48.9115s/init5.81587s/query43.09563s,232,042.09requests/CPU-second,RSS1,389,133,824bytes,files99,812,292bytes. RelativeV90query37.6486s,14.47%slower for0.14566scoregain. Single-runresearchmeasurementsdonotprovehiddenworkloadperformance.128/256fileswouldexceed100MB withoutothercompressionchanges.

A separateJOINT_CELL_ALIGN32compilevariant pads18-byte long-longrecords to32bytes,avoiding cache-linestraddling and simplifying indexing. Defaultalignment2 preserves18-byteformat. It adds172,032,000bytesRAMrelative18-byte record, so memory mustbemeasuredagainst2GB. benchmark_aligned_joint_correction.py verifiesfullvalidationparitybeforeactual10m. Layoutexperimentdoesnotchangeasset/predictionsemanticsorproveacachecausewithouttimingevidence.

##32-byte outcome and retention decision
64treefullvalidationbyte-exact. Actual10m totalCPU48.4547s/init5.75173s/query42.70297s,234,175.75/s,RSS1,561,116,672bytes,files99,812,476bytes. Querygain0.91%against18-byte single-runmeasurement,withinplausiblerunvariation,whileRAMincreases171,982,848bytes. Do notretain32asdefaultorclaimlinestraddlingwasprovenmainbottleneck. Jointarchitectureaccuracyimprovementisretainedasoptionalresearchcandidate; timingtargetand99.9remainunmet. Needhigherprecisionandlessquerycost; strongeraccuracy128/256variantsarenotfile-budgetcompliantcurrently. Alljobscompleted,nofullbillionrun.
