"""Embed ONLY the five architecture JSON files in the standalone executable."""
import argparse
import hashlib
import json
from pathlib import Path
from architecture import Architecture, DEFAULT_ARCH


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arch', type=Path, default=DEFAULT_ARCH)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    a = Architecture(args.arch)
    vectors = sorted({(n['delta x'], n['delta y']) for n in a.nets})
    fingerprint = hashlib.sha256(b''.join(p.read_bytes() for p in sorted(args.arch.glob('SRB_*.json')))).hexdigest()
    lines = ['// Generated from architecture JSON only. No request or answer data.', '#pragma once',
             'namespace archdata {', f'constexpr int WIDTH={a.width}, HEIGHT={a.height}, P={len(a.ports)}, K={len(vectors)};',
             f'constexpr char HASH[]="{fingerprint}";',
             'struct XY {int x,y;};', 'struct Arc {int from,to,delay;};',
             'struct Net {int from,to,vector,delay;};',
             'struct Line {bool vertical; int site,delay;};',
             'struct Block {int left,right,lower,upper; bool hcross,vcross; int hdelay,vdelay;};']
    def array(kind, name, rows):
        lines.append(f'constexpr {kind} {name}[]={{')
        lines.extend('  {' + ','.join(str(x).lower() for x in row) + '},' for row in rows)
        lines.append('};')
    lines.append('constexpr const char* PORTS[]={' + ','.join(json.dumps(p['Name']) for p in a.ports) + '};')
    array('XY', 'SITES', ((p['x'], p['y']) for p in a.instances))
    array('XY', 'VECTORS', vectors)
    array('Arc', 'ARCS', ((a.port_ids[p['from']], a.port_ids[p['to']], p['delay']) for p in a.arcs))
    array('Net', 'NETS', ((a.port_ids[p['from']], a.port_ids[p['to']], vectors.index((p['delta x'], p['delta y'])), p.get('delay', 0)) for p in a.nets))
    array('Line', 'LINES', ((p['direction']=='vertical', p['site'], p['delay']) for p in a.lines))
    array('Block', 'BLOCKS', ((p['left'], p['right'], p['lower'], p['upper'], p['horizontal crossable'], p['vertical crossable'], p['horizontal cross delay'], p['vertical cross delay']) for p in a.blocks))
    lines.append('}')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('\n'.join(lines) + '\n')
    print(f'Architecture embedded: {len(a.instances)} sites, sha256={fingerprint}')


if __name__ == '__main__':
    main()
