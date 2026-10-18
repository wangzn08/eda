"""Record completed native pipeline measurements without mixing timing scopes."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reference='a1527ca3fb6940f4c6df9d91e60d5ec14210b24d928d676997e9ff1ff8cf2d83'
methods={223:'Circular Dial initialization and chosen-route feature prefetch; original lazy forest',224:'Targeted feature prefetch and eager137 features; sequential forest',226:'Exact9-bit row deltas with sparse10th bits; local16-bit source-mask catalogues; eager interleaved forest',227:'Integer-equivalent compiled8-tree forest',228:'Exhaustive architecture-derived terminal winner-set masks over all integer displacement groups',231:'CTZ candidate iteration and deduplicated response-feature prefetch'}
report={'state':'complete','scope':'Full150053-row native validation profiling; these small-query timings are not standard billion throughput','holdout_used':False,'reference_score':99.51665300760335,'reference_sha256':reference,'cases':[]}
for version,method in methods.items():
 folder=ROOT/f'out/v{version}';log=folder/'validation.stderr';csv=folder/'validation.csv'
 if not log.exists() or not csv.exists():continue
 text=log.read_text();m=re.search(r'rows=(\d+) cpu_seconds=([0-9.]+) initialization_seconds=([0-9.]+)',text)
 if not m:continue
 h=hashlib.sha256(csv.read_bytes()).hexdigest();item={'version':version,'method':method,'rows':int(m[1]),'cpu_seconds':float(m[2]),'initialization_seconds':float(m[3]),'query_seconds':float(m[2])-float(m[3]),'output_sha256':h,'all_validation_output_bytes_equal_v219':h==reference,'score':99.51665300760335 if h==reference else None,'peak_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',text)[1]),'components':{key:float(value) for key,value in re.findall(r'(component_\w+)=([0-9.]+)',text)}};report['cases'].append(item)
(ROOT/'reports/V223-V231-native-pipeline-profiles.json').write_text(json.dumps(report,indent=2)+'\n')
short={'state':'complete','scope':'Independent full frozen11-bit short-field row-range scan; new representation separately checked through native validation parity','rows':4247840,'entries':679654400,'row_span_max':701,'rows_by_required_bits':{'8':9,'9':4212481,'10':35350},'old_scalar_data_bytes':934524800,'new_low9_data_bytes':764611200,'new_row_descriptor_bytes':16991360,'new_sparse_high_plane_bytes':707000,'new_total_data_bytes':782309560,'saved_bytes':152215240,'source_mask_entries':40771584,'source_local_patterns':1091416,'max_patterns_per_source':28516,'source_old_mask_bytes':163086336,'source_new_code_bytes':81543168,'source_new_pattern_bytes':4365664,'source_new_start_bytes':192}
(ROOT/'reports/V226-short-rows-and-source-catalog.json').write_text(json.dumps(short,indent=2)+'\n')
print('Recorded native pipeline and complete row-range audit')
