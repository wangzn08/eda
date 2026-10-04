"""Repeat a request-only public million file 1000 times; no golden input."""
import hashlib,json,time
from architecture import ROOT

def main():
    root=ROOT/'out/acceptance-v14'
    source=root/'public.request.csv'
    data=source.read_bytes();header,body=data.split(b'\n',1)
    assert header.rstrip(b'\r')==b'From,To'
    assert body.count(b'\n')==1000000 and body.endswith(b'\n')
    start=time.monotonic();target=root/'stress1b.request.csv'
    with target.open('wb') as f:
        f.write(header+b'\n')
        for i in range(1000):
            f.write(body)
            if (i+1)%100==0:print(f'Prepared {i+1} million rows',flush=True)
    (root/'stress-input.json').write_text(json.dumps({'rows':1000000000,'repetitions':1000,
        'source':str(source),'source_sha256':hashlib.sha256(data).hexdigest(),
        'bytes':target.stat().st_size,'generation_seconds':time.monotonic()-start},indent=2)+'\n')

if __name__=='__main__':main()
