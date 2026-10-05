"""Prepare the selected fast research profile; no formal submission acceptance."""
import hashlib,json,shutil
from architecture import ROOT

def main():
    folder=ROOT/'out/phase-fast-v50';folder.mkdir(exist_ok=True);files={}
    for source,name in [('build/phase_fast_estimate','estimate'),('models/phase-bounds-safe.bin','phase-bounds.bin'),('models/fast-residual-v50.bin','residual.bin')]:
        target=folder/name;shutil.copy2(ROOT/source,target);files[name]={'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    manifest={'profile':'V50 256 trees','runtime_bytes':sum(v['bytes'] for v in files.values()),'files':files,'validation_score':96.93292509763232,'scope':'Approximate candidate, not final submission acceptance'}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (folder/'README.md').write_text('V50 fast approximate candidate, 256 trees.\nRun: ./estimate -in requests.csv -out result.csv\nDefault: no result cache. Assets beside executable.\nValidation96.9329; V40 precision profile is retained separately.\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
