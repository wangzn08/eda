"""Reference interpretation of V0.3 geometry; used for data auditing only."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCH = ROOT / 'data/EDA-PANGO-SRB-Arch-Delay/arch'


class Architecture:
    def __init__(self, directory=DEFAULT_ARCH):
        def read(name, key):
            return json.loads((Path(directory) / name).read_text())[key]
        self.instances = read('SRB_Inst.json', 'Inst')
        self.ports = read('SRB_Port.json', 'Port')
        self.arcs = read('SRB_Arc.json', 'Arcs')
        self.nets = read('SRB_Net.json', 'Nets')
        self.gaps = read('SRB_Gap.json', 'Gap')
        self.lines = self.gaps['Line']
        self.blocks = self.gaps['Block']
        self.coordinates = {i['name']: (i['x'], i['y']) for i in self.instances}
        self.sites = {v: k for k, v in self.coordinates.items()}
        self.port_ids = {p['Name']: i for i, p in enumerate(self.ports)}
        self.instance_ids = {p['name']: i for i, p in enumerate(self.instances)}
        self.width = max(i['x'] for i in self.instances) + 1
        self.height = max(i['y'] for i in self.instances) + 1
        self.arc_delays = {}
        for a in self.arcs:
            pair = a['from'], a['to']
            self.arc_delays[pair] = min(a['delay'], self.arc_delays.get(pair, a['delay']))
        self.net_by_from = {}
        for n in self.nets:
            self.net_by_from.setdefault(n['from'], []).append(n)

    def pin(self, text):
        instance, port = text.strip().split('/')
        return self.coordinates[instance], port, self.instance_ids[instance] * len(self.ports) + self.port_ids[port]

    def block_at(self, x, y):
        return next((b for b in self.blocks if b['left'] <= x <= b['right'] and b['lower'] <= y <= b['upper']), None)

    def move(self, x, y, dx, dy):
        if bool(dx) == bool(dy):
            raise ValueError('Expected exactly one nonzero displacement axis')
        sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
        axis = 'horizontal' if dx else 'vertical'
        steps, delay = abs(dx) + abs(dy), 0
        ox, oy = x, y
        crossed = set()
        while steps:
            x += sx
            y += sy
            if not (0 <= x < self.width and 0 <= y < self.height):
                return None
            block = self.block_at(x, y)
            if block and block[axis + ' crossable']:
                if block['id'] not in crossed:
                    delay += block[axis + ' cross delay']
                    crossed.add(block['id'])
            else:
                steps -= 1
        if (x, y) not in self.sites:
            return None
        for line in self.lines:
            lo, hi = sorted((ox, x) if line['direction'] == 'vertical' else (oy, y))
            if lo <= line['site'] < hi:
                delay += line['delay']
        return (x, y), delay

    def edge_delay(self, source, target):
        (x, y), sp, _ = self.pin(source)
        destination, tp, _ = self.pin(target)
        candidates = []
        if destination == (x, y) and (sp, tp) in self.arc_delays:
            candidates.append(self.arc_delays[sp, tp])
        for net in self.net_by_from.get(sp, []):
            moved = self.move(x, y, net['delta x'], net['delta y'])
            if moved and moved[0] == destination and net['to'] == tp:
                candidates.append(moved[1] + net.get('delay', 0))
        if not candidates:
            raise ValueError(f'No directed edge: {source} -> {target}')
        return min(candidates)
