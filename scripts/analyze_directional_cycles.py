"""Find minimum cost/displacement cycles in direction-only architecture graphs."""
import json
from architecture import Architecture, ROOT


def main():
    arch = Architecture()
    net_by_output = {n['from']: n for n in arch.nets}
    report = {'scope': 'Architecture-only directional cycles; mixed-direction cycles not covered', 'directions': {}}
    for name, axis, sign in [('east', 'delta x', 1), ('west', 'delta x', -1),
                             ('north', 'delta y', 1), ('south', 'delta y', -1)]:
        other = 'delta y' if axis == 'delta x' else 'delta x'
        nets = [n for n in arch.nets if n[axis]*sign > 0 and n[other] == 0]
        ports = sorted(set(n['to'] for n in nets))
        index = {p: i for i, p in enumerate(ports)}
        edges = []
        for arc in arch.arcs:
            n = net_by_output.get(arc['to'])
            if arc['from'] in index and n in nets:
                edges.append((index[arc['from']], index[n['to']], arc['delay']+n.get('delay', 0), abs(n[axis]), arc, n))
        def cycle(ratio):
            distance = [0.]*len(ports)
            predecessor = [None]*len(ports)
            last = None
            for _ in ports:
                last = None
                for ei, (u, v, cost, span, _, _) in enumerate(edges):
                    value = distance[u]+cost-ratio*span
                    if value < distance[v]-1e-10:
                        distance[v] = value
                        predecessor[v] = ei
                        last = v
                if last is None:
                    return None
            for _ in ports:
                last = edges[predecessor[last]][0]
            start, selected = last, []
            while True:
                ei = predecessor[last]
                selected.append(ei)
                last = edges[ei][0]
                if last == start:
                    return selected[::-1]
        low, high = 0., 1000.
        assert cycle(high) is not None
        for _ in range(40):
            middle = (low+high)/2
            if cycle(middle) is None:
                low = middle
            else:
                high = middle
        selected = cycle(high+1e-7)
        cost = sum(edges[e][2] for e in selected)
        span = sum(edges[e][3] for e in selected)
        report['directions'][name] = {'ports': len(ports), 'edges': len(edges),
                                      'cycle_cost_ps': cost, 'cycle_displacement': span,
                                      'ps_per_cell': cost/span,
                                      'cycle': [{'from': ports[edges[e][0]], 'to': ports[edges[e][1]],
                                                 'arc': edges[e][4], 'net': edges[e][5]} for e in selected]}
    (ROOT/'reports/directional-cycle-ratios.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: {a: b for a, b in v.items() if a != 'cycle'}
                      for k, v in report['directions'].items()}, indent=2))


if __name__ == '__main__':
    main()
