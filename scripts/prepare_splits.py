"""Persist reproducible disjoint splits; inference inputs contain no labels."""
import collections
import csv
import hashlib
import json
from contextlib import ExitStack
from architecture import DEFAULT_ARCH, ROOT
from audit_data import partition


def main():
    directory=ROOT/'out/evaluation'
    directory.mkdir(parents=True,exist_ok=True)
    counts=collections.Counter()
    with ExitStack() as stack:
        writers={}
        for split in ('development','validation','holdout'):
            writers[split]=[]
            for suffix,fields in (('request',['From','To']),('golden',['From','To','delay'])):
                f=stack.enter_context((directory/f'{split}.{suffix}.csv').open('w',newline=''))
                w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
                w.writeheader(); writers[split].append(w)
        f=stack.enter_context((DEFAULT_ARCH.parent/'data/delay_estimate_ans.csv').open(newline=''))
        for row in csv.DictReader(f):
            name=partition(row['From'].strip(),row['To'].strip())
            for writer in writers[name]: writer.writerow(row)
            counts[name]+=1
    files={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(directory.glob('*.csv'))}
    report={'partition':'BLAKE2b-64(From + NUL + To), little-endian modulo 100; <70 development, <85 validation, otherwise holdout',
            'counts':dict(counts),'files':files,'note':'Splits prepared only; no validation or holdout predictions evaluated.'}
    (directory/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'directory':str(directory),'counts':dict(counts)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
