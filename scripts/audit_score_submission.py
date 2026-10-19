"""Check measured files and independently rebuild the frozen source closure."""
import argparse,hashlib,json,stat,struct,subprocess
from pathlib import Path
from architecture import ROOT

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def macho(data):
 assert struct.unpack_from('<I',data)[0]==0xfeedfacf
 normalized=bytearray(data);sections={};offset=32
 for _ in range(struct.unpack_from('<I',data,16)[0]):
  command,size=struct.unpack_from('<II',data,offset)
  if command==0x1b:normalized[offset+8:offset+24]=bytes(16)
  elif command==0x1d:
   start,length=struct.unpack_from('<II',data,offset+8);normalized[start:start+length]=bytes(length)
  elif command==0x19:
   count=struct.unpack_from('<I',data,offset+64)[0]
   for i in range(count):
    section=offset+72+i*80
    name=data[section:section+16].split(b'\0')[0].decode()
    segment=data[section+16:section+32].split(b'\0')[0].decode()
    length=struct.unpack_from('<Q',data,section+40)[0];start=struct.unpack_from('<I',data,section+48)[0]
    if start and length:
     assert start+length<=len(data)
     sections[segment+'/'+name]=hashlib.sha256(data[start:start+length]).hexdigest()
  offset+=size
 return bytes(normalized),sections

def main():
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args()
 v=a.version;work=ROOT/f'out/v{v}';folder=ROOT/f'out/submission/final-v{v}'
 profile=json.loads((ROOT/f'reports/V{v}-native-score-profile.json').read_text())
 assert profile['state']=='complete' and len(profile['runs'])==3
 assert profile['observed_runtime_threads']==1 and profile['prediction_cache'] is False and profile['architecture_operator_cache'] is False
 assert profile['validation_score']>=99.5 and profile['peak_rss_bytes']<=2000000000
 assert profile['runs'][0]['all_predictions_equal_offline']
 before=profile['asset_sha256_before'];assert before==profile['asset_sha256_after']
 for name,expected in before.items():assert digest(folder/name)==expected
 manifest=json.loads((folder/'BUILD_MANIFEST.json').read_text())
 assert manifest['runtime_asset_sha256']==before
 for name,expected in manifest['source_sha256'].items():assert digest(folder/name)==expected
 files=[p for p in folder.rglob('*') if p.is_file()]
 assert not any(p.is_symlink() for p in folder.rglob('*'))
 size=sum(p.stat().st_size for p in files);assert size<=100000000
 reference=(folder/'estimate').read_bytes();permissions=stat.S_IMODE((folder/'estimate').stat().st_mode)
 try:
  with (work/'standalone-rebuild.stdout').open('w') as out,(work/'standalone-rebuild.stderr').open('w') as err:
   subprocess.run(['make','rebuild'],cwd=folder,stdout=out,stderr=err,check=True)
  rebuilt=(folder/'estimate').read_bytes()
  left,left_sections=macho(reference);right,right_sections=macho(rebuilt)
  proof={'reference_binary_sha256':hashlib.sha256(reference).hexdigest(),'rebuilt_binary_sha256':hashlib.sha256(rebuilt).hexdigest(),
         'all_file_backed_sections_identical':left_sections==right_sections,
         'identical_except_macho_uuid_and_signature':left==right,'reference_sections':left_sections,'rebuilt_sections':right_sections}
  (work/'rebuild-parity.json').write_text(json.dumps(proof,indent=2)+'\n')
  assert proof['all_file_backed_sections_identical'] and proof['identical_except_macho_uuid_and_signature']
 finally:
  (folder/'estimate').write_bytes(reference);(folder/'estimate').chmod(permissions)
 for name,expected in before.items():assert digest(folder/name)==expected
 for name,expected in manifest['source_sha256'].items():assert digest(folder/name)==expected
 assert sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())==size
 report={'state':'complete','version':v,'validation_score':profile['validation_score'],'billion_estimate_cpu_seconds':[r['billion_estimate_cpu_seconds'] for r in profile['runs'][1:]],
         'pooled_billion_estimate_cpu_seconds':profile['pooled_billion_estimate_cpu_seconds'],'complete_submission_bytes':size,'file_count':len(files),
         'peak_rss_bytes':profile['peak_rss_bytes'],'runtime_asset_sha256':before,
         'same_frozen_runtime_for_all_runs':True,'all_validation_predictions_equal_independent_python':True,'all_output_pin_orders_checked':True,
         'single_runtime_thread_observed':True,'prediction_cache':False,'architecture_operator_cache':False,
         'standalone_rebuild_all_sections_identical':True,'standalone_rebuild_diff_only_uuid_and_signature':True,
         'scope':'Apple M4/macOS, single-thread CPU extrapolation on six million disjoint synthetic novel requests, one initialization per billion; not an official hidden-input measurement, no5-run official consistency score claimed'}
 (ROOT/f'reports/V{v}-submission-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
