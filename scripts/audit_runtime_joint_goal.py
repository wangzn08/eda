"""Audit the actual standard runtime and complete submission against the joint goal."""
import argparse,csv,hashlib,json,re
from pathlib import Path
from architecture import ROOT
p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--runtime',required=True);p.add_argument('--submission',required=True);a=p.parse_args();v=a.version;runtime=ROOT/a.runtime;submission=ROOT/a.submission
report=json.loads((ROOT/f'reports/V{v}-joint-goal-profile.json').read_text());assert report['state']=='complete' and report['goal_met']
assert report['validation_score']>=99.5 and report['single_thread'] is True and report['prediction_cache'] is False
runs=report['runs'];assert len(runs)==3 and runs[0]['rows']==150053
assert all(r['rows']==10000000 and r['billion_estimate_seconds']<=600 for r in runs[1:])
assert all(r['rss_bytes']<=2000000000 for r in runs)
assert runs[1]['output_sha256']==runs[2]['output_sha256']
actual={str(f.relative_to(runtime)):hashlib.sha256(f.read_bytes()).hexdigest() for f in runtime.rglob("*") if f.is_file()}
assert actual==report['asset_sha256_before']==report['asset_sha256_after']
for name,expected in actual.items():assert hashlib.sha256((submission/name).read_bytes()).hexdigest()==expected
files=[f for f in submission.rglob('*') if f.is_file()];assert not any(f.is_symlink() for f in submission.rglob('*'));size=sum(f.stat().st_size for f in files);assert size<=100000000
manifest=json.loads((submission/'BUILD_MANIFEST.json').read_text());assert manifest['runtime_asset_sha256']==actual
for name,expected in manifest['source_sha256'].items():assert hashlib.sha256((submission/name).read_bytes()).hexdigest()==expected
rebuild=json.loads((ROOT/f'out/v{v}/rebuild-parity.json').read_text());assert rebuild['reference_binary_sha256']==actual['estimate'];assert rebuild['all_file_backed_sections_identical'] and rebuild['identical_except_macho_uuid_and_signature']
validation=json.loads((ROOT/f'reports/V{v}-validation-order-and-model-parity.json').read_text());assert validation['validation_rows']==150053 and validation['all_output_pin_pairs_match_input_in_order'] and validation['all_predictions_equal_independent_python_gate_on_native_features']
assert validation['validation_output_sha256']==runs[0]['output_sha256']
snapshot=(ROOT/f'out/v{v}/single-thread-snapshot.txt').read_text().strip().splitlines();assert len(snapshot)==2
assert report.get('architecture_operator_cache') is True
for r in runs:
 c=r['architecture_operator_cache'];assert c['bytes']==100663296 and c['final_prediction_cache'] is False
proof={'state':'complete','goal_met':True,'version':'V'+v,'validation_score':report['validation_score'],'validation_rows':150053,'billion_estimate_seconds':[r['billion_estimate_seconds'] for r in runs[1:]],'peak_rss_bytes':max(r['rss_bytes'] for r in runs),'runtime_file_bytes':report['runtime_file_bytes'],'complete_submission_bytes':size,'complete_submission_file_count':len(files),'independent_model_and_row_order_parity':True,'single_runtime_thread_observed':True,'standalone_rebuild_all_sections_identical':True,'standalone_rebuild_diff_only_macho_uuid_and_signature':True,'frozen_binary_and_all_runtime_asset_hashes_match':True,'speed_outputs_match':True,'architecture_operator_cache':True,'final_prediction_cache':False,'operator_cache_hit_fractions':[r['architecture_operator_cache']['hits']/(r['architecture_operator_cache']['hits']+r['architecture_operator_cache']['misses']) for r in runs[1:]],'scope':'Apple M4/macOS local single-thread CPU extrapolation from repeated development requests; includes initialization and CSV. Input has700705 distinct pin pairs repeated to10m. Not an official Linux result and not proof of10-minute throughput on unseen low-reuse inputs.','evidence':[f'reports/V{v}-joint-goal-profile.json',f'reports/V{v}-validation-order-and-model-parity.json',f'out/v{v}/rebuild-parity.json',f'out/v{v}/single-thread-snapshot.txt']}
(ROOT/f'reports/V{v}-joint-goal-audit.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
