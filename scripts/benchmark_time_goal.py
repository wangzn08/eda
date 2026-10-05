"""One full file-based run; predictions recomputed per row, no gold labels read."""
import argparse,hashlib,json,os,platform,re,signal,subprocess,time
from pathlib import Path
from architecture import ROOT

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(8<<20):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--rows',type=int,required=True);a=p.parse_args()
    exe=ROOT/'out/phase-fast-v50/estimate';log=a.report.with_suffix('.log');command=[str(exe),'-in',str(a.input),'-out',str(a.output),'--no-cache','--progress']
    report={'state':'running','rows_expected':a.rows,'profile':'V50 256 trees','cache':False,'single_thread_solver':True,'machine':platform.platform(),'command':command,'binary_sha256':digest(exe),'input_bytes':a.input.stat().st_size,'scope':'Development requests repeated; no result cache, every row predicted; not arbitrary unique hidden requests or official platform acceptance.'}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);start=time.monotonic()
    with log.open('wb') as f:
        process=subprocess.Popen(['/usr/bin/time','-l',*command],stderr=f,start_new_session=True)
        report['pid']=process.pid;a.report.write_text(json.dumps(report,indent=2)+'\n')
        try:code=process.wait(timeout=4200)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM);process.wait();report['state']='timeout';a.report.write_text(json.dumps(report,indent=2)+'\n');raise
    text=log.read_text();match=re.search(r'rows=(\d+) cpu_seconds=([\d.]+)',text);rss=re.search(r'(\d+)\s+maximum resident set size',text)
    if code or not match or int(match[1])!=a.rows:report['state']='failed';report['exit_code']=code;a.report.write_text(json.dumps(report,indent=2)+'\n');raise RuntimeError('Incomplete benchmark')
    report.update(state='checking_output',cpu_seconds=float(match[2]),wall_seconds=time.monotonic()-start,rss_bytes=int(rss[1]),output_bytes=a.output.stat().st_size);a.report.write_text(json.dumps(report,indent=2)+'\n')
    h=hashlib.sha256();lines=0
    with a.output.open('rb') as f:
        header=f.readline();assert header==b'From,To,delay\n';h.update(header)
        while b:=f.read(8<<20):lines+=b.count(b'\n');h.update(b)
    assert lines==a.rows
    report.update(state='complete',rows_written=lines,output_sha256=h.hexdigest(),within_one_hour_cpu=report['cpu_seconds']<=3600,within_2GB=report['rss_bytes']<=2*1024**3)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
