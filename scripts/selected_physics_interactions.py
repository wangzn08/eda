"""Integer endpoint/curve interactions, shared by research and C++ export.

These are input features, not certified shortest path bounds. Potential sums
are inspired by endpoint decomposition; none is used to prune a feasible path.
"""
import numpy as np


def specifications():
    specs = []
    for mode in range(2):
        for depth in range(3):
            s, t = 125 + mode * 3 + depth, 131 + mode * 3 + depth
            for op in ('sum', 'max', 'min', 'difference'):
                specs.append((f'endpoint_{op}_{mode}_{depth}', op, s, t))
        for side, start in [('source', 125), ('target', 131)]:
            for depth in (1, 2):
                specs.append((f'{side}_phi_growth_{mode}_{depth}', 'difference',
                              start + mode * 3 + depth, start + mode * 3))
    for j in range(6):
        specs.append((f'intrinsic_minus_response_{j}', 'intrinsic', 69 + j, 0))
    for a, b in ((69, 70), (70, 71), (71, 72), (72, 73), (73, 74)):
        specs.append((f'response_growth_{a}_{b}', 'difference', b, a))
    for name, v, axis in [('source_x', 63, 19), ('source_y', 64, 20),
                           ('end_x', 66, 19), ('end_y', 67, 20)]:
        specs.append((f'vector_toward_target_{name}', 'aligned', v, axis))
    specs.extend([('bank_x', 'bank_x', 0, 0), ('bank_abs_x', 'bank_abs_x', 0, 0),
                  ('bank_x_mod10', 'bank_x_mod10', 0, 0)])
    return specs


def augment(x):
    raw = np.rint(x * np.where(np.arange(137) >= 77, 12, 1)).astype(np.int32)
    sign = lambda a: np.sign(a).astype(np.int32)
    intrinsic = raw[:, 44] - raw[:, 45] - (raw[:, 46] == 2) * 292 - raw[:, 24] * np.where(raw[:, 20] < 0, 125, 127)
    bank_x = raw[:, 19] - (raw[:, 46] == 2) * sign(raw[:, 19]) * 14
    extras = []
    for _, op, a, b in specifications():
        if op == 'sum': value = raw[:, a] + raw[:, b]
        elif op == 'max': value = np.maximum(raw[:, a], raw[:, b])
        elif op == 'min': value = np.minimum(raw[:, a], raw[:, b])
        elif op == 'difference': value = raw[:, a] - raw[:, b]
        elif op == 'intrinsic': value = intrinsic - raw[:, a]
        elif op == 'aligned': value = raw[:, a] * sign(raw[:, b])
        elif op == 'bank_x': value = bank_x
        elif op == 'bank_abs_x': value = abs(bank_x)
        elif op == 'bank_x_mod10': value = abs(bank_x) % 10
        else: raise ValueError(op)
        extras.append(value)
    return np.column_stack([x, *extras]).astype(np.float32)


def cpp_header():
    lines = ['#pragma once', '// Generated integer physics interaction features; no path pruning.',
             'namespace selectedphysics {',
             'template<class Row> int value(Row&r,unsigned index){',
             'auto f=[&](unsigned i){return int(r.get(i));};',
             'auto raw=[&](unsigned i){return i>=77?int(std::nearbyint(double(r.get(i))*12.0)):f(i);};',
             'auto sign=[](int x){return (x>0)-(x<0);};',
             'auto bank_x=[&](){return f(19)-(f(46)==2?sign(f(19))*14:0);};',
             'switch(index){']
    for i, (_, op, a, b) in enumerate(specifications()):
        if op == 'sum': expression = f'raw({a})+raw({b})'
        elif op in ('max', 'min'): expression = f'std::{op}(raw({a}),raw({b}))'
        elif op == 'difference': expression = f'raw({a})-raw({b})'
        elif op == 'intrinsic': expression = f'f(44)-f(45)-(f(46)==2?292:0)-f(24)*(f(20)<0?125:127)-f({a})'
        elif op == 'aligned': expression = f'f({a})*sign(f({b}))'
        elif op == 'bank_x': expression = 'bank_x()'
        elif op == 'bank_abs_x': expression = 'std::abs(bank_x())'
        elif op == 'bank_x_mod10': expression = 'std::abs(bank_x())%10'
        else: raise ValueError(op)
        lines.append(f'case {i}:return {expression};')
    lines += ['default:throw std::runtime_error("Physics feature index");', '}', '}']
    lines += ['template<unsigned Index,class Row> int integer(Row&r){',
              f'static_assert(Index<{len(specifications())});']
    def access(i):
        return f'r.template integer<{i}>()'
    for i, (_, op, a, b) in enumerate(specifications()):
        av, bv = access(a), access(b)
        s = f'(({access(19)}>0)-({access(19)}<0))'
        bank = f'({access(19)}-({access(46)}==2?{s}*14:0))'
        if op == 'sum': expression = f'{av}+{bv}'
        elif op in ('max', 'min'): expression = f'std::{op}({av},{bv})'
        elif op == 'difference': expression = f'{av}-{bv}'
        elif op == 'intrinsic': expression = f'{access(44)}-{access(45)}-({access(46)}==2?292:0)-{access(24)}*({access(20)}<0?125:127)-{av}'
        elif op == 'aligned': expression = f'{av}*(({bv}>0)-({bv}<0))'
        elif op == 'bank_x': expression = bank
        elif op == 'bank_abs_x': expression = f'std::abs({bank})'
        elif op == 'bank_x_mod10': expression = f'std::abs({bank})%10'
        else: raise ValueError(op)
        lines.append(('if' if i == 0 else 'else if') + f' constexpr(Index=={i})return {expression};')
    lines += ['}', '}']
    return '\n'.join(lines) + '\n'
