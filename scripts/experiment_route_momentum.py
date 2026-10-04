"""Fit V2 residuals using first/last Net directions from the official graph."""
import collections
import json
import time

from architecture import Architecture, ROOT
from experiment_displacement import weighted_score
from experiment_region_port import load


def encode(direction, dx, dy):
    if direction is None:
        return 0
    vx, vy = direction
    projection = vx * dx + vy * dy
    return 1 if projection > 0 else 2 if projection < 0 else 3


def key(row, kind, outgoing, incoming):
    sx, sy, tx, ty, sp, tp, _, _ = row
    dx, dy = tx - sx, ty - sy
    distance = abs(dx) + abs(dy)
    bucket = 0 if distance < 16 else 1 if distance < 64 else 2 if distance < 256 else 3
    source = encode(outgoing.get(sp), dx, dy)
    target = encode(incoming.get(tp), dx, dy)
    xsign, ysign = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
    if kind == 'momentum':
        return source, target, bucket, xsign, ysign
    if kind == 'source_port_momentum':
        return sp if source else 'other', source, bucket, xsign, ysign
    if kind == 'target_port_momentum':
        return tp if target else 'other', target, bucket, xsign, ysign
    if kind == 'both_port_momentum':
        return sp if source else 'other', tp if target else 'other', bucket
    if kind == 'axis_span':
        s = outgoing.get(sp)
        t = incoming.get(tp)
        return (abs(s[0]+s[1]) if s else 0, abs(t[0]+t[1]) if t else 0,
                source, target, bucket)
    raise ValueError(kind)


def fit(rows, kind, prior, outgoing, incoming):
    sums = collections.defaultdict(lambda: [0., 0])
    for row in rows:
        if row[6] <= 0:
            continue
        entry = sums[key(row, kind, outgoing, incoming)]
        entry[0] += row[6] - row[7]
        entry[1] += 1
    return {k: total / (count + prior) for k, (total, count) in sums.items()}


def evaluate(rows, kind, table, outgoing, incoming):
    total = 0.
    groups = collections.defaultdict(lambda: [0., 0])
    for row in rows:
        if row[6] <= 0:
            continue
        value = table.get(key(row, kind, outgoing, incoming), 0)
        pred = max(0, round(row[7] + value))
        score = weighted_score(row[6], pred)
        total += score
        distance = abs(row[2]-row[0])+abs(row[3]-row[1])
        bucket = '0-15' if distance < 16 else '16-63' if distance < 64 else '64-255' if distance < 256 else '256+'
        groups[bucket][0] += score
        groups[bucket][1] += 1
    return {'score': total / len(rows),
            'by_distance': {k: {'score': total/count, 'rows': count}
                            for k, (total, count) in groups.items()}}


def main():
    start = time.monotonic()
    arch = Architecture()
    outgoing = {n['from']: (n['delta x'], n['delta y']) for n in arch.nets}
    incoming = {n['to']: (n['delta x'], n['delta y']) for n in arch.nets}
    dev, val = load('development', 'v2'), load('validation', 'v2')
    candidates=[]
    for kind in ('momentum','source_port_momentum','target_port_momentum',
                 'both_port_momentum','axis_span'):
        for prior in (20,100):
            table=fit(dev,kind,prior,outgoing,incoming)
            candidates.append({'kind':kind,'prior':prior,'entries':len(table),
                               'metrics':evaluate(val,kind,table,outgoing,incoming)})
    report={'description':'first/last Net direction derived from official architecture',
            'baseline':evaluate(val,'momentum',{},outgoing,incoming),
            'candidates':candidates,'elapsed_seconds':time.monotonic()-start,
            'holdout_used':False}
    (ROOT/'reports/V3-route-momentum.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'baseline':report['baseline']['score'],
                      'candidates':[(c['kind'],c['prior'],c['metrics']['score']) for c in candidates]},indent=2))


if __name__=='__main__':main()
