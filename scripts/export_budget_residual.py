"""Compile small numeric LightGBM corrections with integer-exact split cuts."""
import argparse,math,json,hashlib
from pathlib import Path
import lightgbm as lgb
p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('output');p.add_argument('--cutoff',type=float,default=0);a=p.parse_args()
m=lgb.Booster(model_file=a.model);d=m.dump_model();assert d['max_feature_idx']<56
def leaves(node):
 if 'leaf_value' in node:return [float(node['leaf_value'])]
 return leaves(node['left_child'])+leaves(node['right_child'])
integer_single=len(d['tree_info'])==1
assert a.cutoff>=0 and (integer_single or a.cutoff==0)
assert all(abs(v)<1e8 for t in d['tree_info'] for v in leaves(t['tree_structure']))
lines=['#pragma once','#include "budget_residual_features.hpp"',f'// LightGBM model SHA256: {hashlib.sha256(Path(a.model).read_bytes()).hexdigest()}']
for i,t in enumerate(d['tree_info']):
 return_type='int' if integer_single else 'double'
 lines.append(f'__attribute__((noinline)) static {return_type} budget_tree_{i}(const BudgetResidualFeatures&r){{')
 def emit(n):
  if 'leaf_value' in n:
   v=float(n['leaf_value']);v=0. if abs(v)<=a.cutoff else v
   if integer_single:
    # For |base|<=1e9, double addition has <1e-6 absolute rounding error.
    # All leaves safely away from half-integers can be rounded once here.
    # Near ties retain the original base-dependent IEEE nearest-even result.
    value=str(round(v)) if abs((v-math.floor(v))-.5)>1e-6 else f'int(std::nearbyint(double(r.b)+{v.hex()}))-r.b'
   else:value=v.hex()
   lines.append(f'return {value};');return
  assert n['decision_type']=='<=' and n['missing_type'] in ('None','NaN')
  lines.append(f'if(r.integer<{n["split_feature"]}>()<={math.floor(float(n["threshold"]))}){{');emit(n['left_child']);lines.append('}else{');emit(n['right_child']);lines.append('}')
 emit(t['tree_structure']);lines.append('}')
lines+=['static int budget_correct(Node from,Node to,int base){BudgetResidualFeatures r(from,to,base);'+('return std::max(0,base+budget_tree_0(r));}' if integer_single else 'double value=0.;')]
for i in range(0 if integer_single else len(d['tree_info'])):lines.append(f'value+=budget_tree_{i}(r);')
if not integer_single:lines+=['return int(std::nearbyint(std::max(0.,double(base)+value)));}']
Path(a.output).write_text('\n'.join(lines)+'\n')
print(json.dumps({'trees':len(d['tree_info']),'single_tree_integer_result':integer_single,'cutoff':a.cutoff,'header_bytes':Path(a.output).stat().st_size}))
