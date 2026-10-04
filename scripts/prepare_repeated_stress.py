"""Generate exactly N request rows by repeating the label-free dev requests."""
import argparse
import hashlib
import json
import time

from experiment_displacement import DATA


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--rows',type=int,required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    if args.rows<1: raise ValueError('rows must be positive')
    source=(DATA/'development.request.csv').read_bytes()
    header,body=source.split(b'\n',1)
    if header.rstrip(b'\r')!=b'From,To': raise ValueError('Invalid source header')
    lines=body.splitlines(keepends=True)
    n=len(lines)
    if n!=700705: raise ValueError('Development partition has changed')
    full,remainder=divmod(args.rows,n)
    start=time.monotonic()
    digest=hashlib.sha256()
    with open(args.out,'wb',buffering=8*1024*1024) as out:
        prefix=b'From,To\n';out.write(prefix);digest.update(prefix)
        for _ in range(full):
            out.write(body);digest.update(body)
        for line in lines[:remainder]:
            out.write(line);digest.update(line)
        out.flush()
    result={'rows':args.rows,'out':args.out,'bytes':__import__('os').path.getsize(args.out),
            'sha256':digest.hexdigest(),'repetitions':full,'tail_rows':remainder,
            'elapsed_seconds':time.monotonic()-start,
            'source':'development.request.csv; no golden labels'}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
