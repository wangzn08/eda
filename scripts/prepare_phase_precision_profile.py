"""Prepare a runnable research profile; does not perform competition acceptance."""
import hashlib,json,shutil,subprocess
from architecture import ROOT

def main():
    subprocess.run(['make','-j1','build/phase_estimate'],cwd=ROOT,check=True)
    folder=ROOT/'out/phase-precision-v40';folder.mkdir(parents=True,exist_ok=True);assets={
      'phase_estimate':ROOT/'build/phase_estimate','phase-bounds.bin':ROOT/'models/phase-bounds-safe.bin','long-tail.bin':ROOT/'out/local-oracle/long-tail-12-dict.bin'}
    manifest=[]
    for name,source in assets.items():
        target=folder/name;shutil.copy2(source,target);manifest.append({'file':name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    (folder/'manifest.json').write_text(json.dumps({'files':manifest,'runtime_bytes':sum(a['bytes'] for a in manifest),'competition_acceptance_done':False},indent=2)+'\n')
    (folder/'README.md').write_text('# V40 精度研究运行目录\n\n默认相对误差上限0.00024；使用与程序同目录的两份资产。\n\n```sh\n./phase_estimate -in requests.csv -out results.csv\n```\n\n只接受From,To请求，不接受标准答案列。正式时间要求和提交包尚未验收。完整固定验证分99.9963756由共用求解器在研究入口上测得；独立入口1001条预测和证书与研究入口逐字节一致。\n')
    print(str(folder))

if __name__=='__main__':main()
