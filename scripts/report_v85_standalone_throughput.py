"""Record finished standard-interface10m benchmark; no extrapolated claim."""
import json,re
from architecture import ROOT
s=(ROOT/'out/v85-profile-speed.log').read_text()
rows=int(re.search(r'rows=(\d+)',s)[1]);assert rows==10000000
cpu=float(re.search('cpu_seconds=([0-9.]+)',s)[1]);init=float(re.search('initialization_seconds=([0-9.]+)',s)[1])
manifest=json.loads((ROOT/'reports/V85-standalone-profile.json').read_text())
r={'rows':rows,'cpu_seconds':cpu,'initialization_seconds':init,'query_cpu_seconds':cpu-init,'requests_per_cpu_second':rows/(cpu-init),'maximum_rss_bytes':int(re.search(r'(\d+)\s+maximum resident set size',s)[1]),'validation_score':manifest['validation_score'],'runtime_file_bytes':manifest['runtime_file_bytes'],'cache_enabled':False,'scope':'Actual standard-interface10m repeated development requests, each recomputed. Single run, no full-billion or hidden workload guarantee.'}
(ROOT/'reports/V85-standalone-throughput.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
