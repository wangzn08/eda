"""Deterministically sample development requests for offline exact route tracing."""
import csv
import heapq
import hashlib
import json

from architecture import ROOT

QUOTAS = {'0-15': 120, '16-63': 160, '64-255': 240, '256+': 80}


def coordinates(pin):
    _, x, y = pin.split('/', 1)[0].split('_')
    return int(x), int(y)


def bucket(row):
    sx, sy = coordinates(row['From'])
    tx, ty = coordinates(row['To'])
    distance = abs(tx - sx) + abs(ty - sy)
    return '0-15' if distance < 16 else '16-63' if distance < 64 else '64-255' if distance < 256 else '256+'


def main():
    selected = {name: [] for name in QUOTAS}
    source = ROOT/'out/evaluation/development.golden.csv'
    with source.open(newline='') as f:
        for row in csv.DictReader(f):
            kind = bucket(row)
            digest = hashlib.blake2b((row['From']+'\0'+row['To']).encode(), digest_size=8,
                                     person=b'route-v3').digest()
            rank = int.from_bytes(digest, 'little')
            heap = selected[kind]
            entry = (-rank, row)
            if len(heap) < QUOTAS[kind]:
                heapq.heappush(heap, entry)
            elif entry[0] > heap[0][0]:
                heapq.heapreplace(heap, entry)
    rows=[]
    for kind in QUOTAS:
        rows.extend(row for _, row in sorted(selected[kind], reverse=True))
    output = ROOT/'out/evaluation/route-v3-development.request.csv'
    golden = ROOT/'out/evaluation/route-v3-development.golden.csv'
    with output.open('w', newline='') as f, golden.open('w', newline='') as g:
        w=csv.DictWriter(f, fieldnames=['From','To']);w.writeheader();w.writerows({'From':r['From'],'To':r['To']} for r in rows)
        v=csv.DictWriter(g, fieldnames=['From','To','delay']);v.writeheader();v.writerows(rows)
    report={'source':'development only','selection':'smallest deterministic BLAKE2b-64 rank per distance bucket',
            'counts':{k:len(selected[k]) for k in QUOTAS},'rows':len(rows),
            'request':str(output),'golden':str(golden),'holdout_used':False}
    (ROOT/'reports/V3-route-sample.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
