"""Select a development-only sample crossing distance, port and Gap categories."""
import collections
import csv
import hashlib
import json
from architecture import Architecture, DEFAULT_ARCH, ROOT
from audit_data import partition
from verify_baseline import write_csv


def main():
    a=Architecture()
    counts=collections.Counter()
    representatives={}
    with (DEFAULT_ARCH.parent/'data/delay_estimate_ans.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            if partition(row['From'],row['To'])!='development': continue
            (x,y),sp,_=a.pin(row['From']); (xx,yy),tp,_=a.pin(row['To'])
            xmin,xmax=sorted((x,xx)); ymin,ymax=sorted((y,yy))
            distance=xmax-xmin+ymax-ymin
            bucket='0-15' if distance<16 else '16-63' if distance<64 else '64-255' if distance<256 else '256+'
            block=any(xmin<=b['right'] and xmax>=b['left'] and ymin<=b['upper'] and ymax>=b['lower'] for b in a.blocks)
            line=any((xmin<=g['site']<xmax) if g['direction']=='vertical' else (ymin<=g['site']<ymax) for g in a.lines)
            region='block_bbox' if block else 'line_span' if line else 'regular'
            key='|'.join((bucket,'INTER' if sp[0] in 'IZ' else 'LOGIC','INTER' if tp[0] in 'IZ' else 'LOGIC',region))
            counts[key]+=1
            representatives.setdefault(key,row)
    keys=sorted(representatives)
    rows=[representatives[k] for k in keys]
    out=ROOT/'out/stress'; out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'request.csv',['From','To'],rows)
    write_csv(out/'golden.csv',['From','To','delay'],rows)
    report={'selection':'First development request in each distance × endpoint types × geometry category; deterministic, no holdout.',
            'geometry_note':'block_bbox and line_span describe endpoint geometry; they do NOT prove the shortest path crosses a particular obstacle.',
            'rows':len(rows),'groups':[{'group':k,'population':counts[k],'sample':representatives[k]} for k in keys],
            'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'request.csv',out/'golden.csv')}}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(rows)} development-only strata; population={sum(counts.values())}')


if __name__=='__main__':
    main()
