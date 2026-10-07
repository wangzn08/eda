# V96/V97: output buffering and exact integer feature bins

## V96 optional CSV writer
--buffered-output assembles rows in1MiB contiguousbuffer and writesblocks viafwrite. It retains normalizedsource/targetstrings, decimaldelayformat andexactLFCSVheader. Explicitfinishcheckswritesandclose; I/Oerrorsexitnonzero. No predictionchangeorresultcache. Fullvalidationbyte-exact. Actual10m totalCPU45.1502s/init5.79371s/query39.35649s,RSS1,389,101,056bytes,files99,813,908. V95query39.46149s:0.27%lessin single runs,insufficientstablegain evidence. Retainasoptionalablation,notdefault.

## V97 exact integer quantization
--integer-bins initializes model-threshold lower_bound results for integerfeatures[-1024,8192],9217entriesperactivefeature,uint16. Feature22isfractionalgeometryresidual andexcluded. Runtimeusesmappedresultonlyforvalidrangeand exactintegerfloatvalue; otherwise originalbinarysearch. Prefixquantizersusedfortruncatedloadedmodelskeeporiginalbinarysearch/rankmapping. Onlymodel-thresholdbinsarecached,notendpointpair/requestpredictions. Tablememoryatmost1.29MiB,noaddedasset. Loaded64model hasnullprefixquantizerforcount64,sofullmodelmappingapplies.

Validationmustcompareall150,053predictionsbyte-exactwithV93trees64(score99.1667785525)before10mactualthroughput. Samearchitectureassets verifiedSHA256againstjointpatchprovenance. Scriptrunsbufferedoutputplusintegerbins; V96servesas output-onlybaseline. Defaultsremainoff. Nochangeinfloatleafaccumulationorrounding.

## Scope
Implementationoptimizations,supportingV93jointarchitecture; notnewlearningalgorithmororiginalshortest-pathmethod. Goal99.9andone-hourbillionunmet. Single-runrepeateddevelopmentthroughputisnotfinalacceptanceorhiddenmixguarantee. No fullbillionrun.

## V97 outcome
Full150,053validationoutputbyte-exacttoV93trees64. Actual10m totalCPU44.1914s/init5.83306s/query38.35834s,260,699.50requests/CPU-second,RSS1,389,805,568bytes,files99,813,860. RelativeV96query39.35649s,2.54%less; relativeV93query43.09563s,10.99%less. Single-runmeasurements,nostatisticalclaim. Throughputstillbelow277,777.78/simpliedone-houraverage;99.9unmet. Retainoptionalinteger-binmapping,numericalparityverified. Jobscompleted;goalactive.
