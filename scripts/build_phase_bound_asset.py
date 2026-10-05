"""Rebuild the safe phase asset from architecture data, without request labels."""
import hashlib,json,subprocess
from architecture import ROOT

def main():
    subprocess.run(['make','-j1','build/build_phase_bounds','build/compress_phase_bounds'],cwd=ROOT,check=True)
    folder=ROOT/'out/architecture-benchmark';folder.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(ROOT/'build/build_phase_bounds'),str(folder/'phase-bounds.raw.bin')],cwd=ROOT,check=True)
    subprocess.run([str(ROOT/'out/research-env/bin/python'),str(ROOT/'scripts/compress_phase_bounds.py')],cwd=ROOT,check=True)
    target=ROOT/'models/phase-bounds-safe.bin'
    subprocess.run([str(ROOT/'build/compress_phase_bounds'),str(folder/'phase-bounds.dictionary.bin'),str(target)],cwd=ROOT,check=True)
    print(json.dumps({'asset':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'golden_used':False},indent=2))

if __name__=='__main__':main()
