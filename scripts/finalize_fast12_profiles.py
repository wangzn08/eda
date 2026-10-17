"""Verify frozen bytes and describe measured local profiles."""
import hashlib,json
from architecture import ROOT
for version in ('115','116'):
 folder=ROOT/f'out/phase-fast12-v{version}';reportpath=ROOT/f'reports/V{version}-fast12-profile.json'
 if not reportpath.exists():continue
 report=json.loads(reportpath.read_text())
 if report['state']!='complete':continue
 manifestpath=folder/'manifest.json';m=json.loads(manifestpath.read_text())
 for name,item in m['files'].items():
  p=folder/name;assert p.stat().st_size==item['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
 m['state']='local 12-minute target passed' if report['goal_met'] else 'target not passed';m['benchmark_report']=str(reportpath.relative_to(ROOT));manifestpath.write_text(json.dumps(m,indent=2)+'\n')
 times=[r['billion_estimate_seconds'] for r in report['runs'][1:]]
 (folder/'README.md').write_text(f'''# V{version} compact delay estimator\n\nUsage: `estimate -in requests.csv -out predictions.csv`. Keep all five `.bin` files beside the executable. Single thread, no prediction-result cache.\n\nValidation score: {report['validation_score']:.10f}; all 150,053 outputs match V112. Actual two serial 10m request runs with CSV I/O; init counted once in billion estimates: {times[0]:.4f} / {times[1]:.4f} CPU seconds. Peak RSS {report['peak_rss_bytes']:,} bytes.\n\nApple M4/macOS local estimates on repeated development requests, not an actual billion run or official Linux result. Ranking and hidden-test accuracy remain unknown. Compiler flags and exact runtime file hashes are in manifest.json. Prior V112 remains in its separate directory.\n''')
 report['runtime_file_bytes']=sum(p.stat().st_size for p in folder.iterdir() if p.is_file());assert report['runtime_file_bytes']<=100000000;report['runtime_asset_hashes_verified']=True;reportpath.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'version':version,'goal_met':report['goal_met'],'runtime_directory_bytes':report['runtime_file_bytes'],'times':times}))
