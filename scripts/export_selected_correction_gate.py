"""Export an exactly thresholded binary model as a simplified correction gate."""
import argparse,json,math,struct
from pathlib import Path
import lightgbm as lgb
p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('mapping');p.add_argument('output');p.add_argument('--threshold',type=float,default=.5);a=p.parse_args();mapping=json.loads(Path(a.mapping).read_text());m=lgb.Booster(model_file=a.model);tree=m.dump_model()['tree_info'];logit=math.log(a.threshold/(1-a.threshold))
def cut(f,t):
 if f<77 or f>=137:return math.floor(t)
 lo,hi=-32769,32768
 while hi-lo>1:
  mid=(lo+hi)//2;v=struct.unpack('<f',struct.pack('<f',mid/12))[0]
  if v<=t:lo=mid
  else:hi=mid
 return lo
def simplify(n):
 if 'leaf_value' in n:return n['leaf_value']>=logit
 assert n['decision_type']=='<='
 left=simplify(n['left_child']);right=simplify(n['right_child'])
 if left==right:return left
 f=mapping[n['split_feature']];assert f<69 or f>=125
 return (f,cut(f,n['threshold']),left,right)
if len(tree)>1:
 lines=['// Development cross-fitted gain gate; exact exported numeric sums.']
 def emit_numeric(n):
  if 'leaf_value' in n:lines.append('return '+float(n['leaf_value']).hex()+';');return
  assert n['decision_type']=='<=';f=mapping[n['split_feature']];assert f<69 or f>=125
  lines.append(f'if(r.integer<{f}>()<={cut(f,n["threshold"])}){{');emit_numeric(n['left_child']);lines.append('}else{');emit_numeric(n['right_child']);lines.append('}')
 for i,t in enumerate(tree):
  lines.append(f'__attribute__((noinline)) static double compiled_gain_gate_{i}(Features&r){{');emit_numeric(t['tree_structure']);lines.append('}')
 lines.append('static bool compiled_needs_correction(Features&r){double sum=0;')
 for i in range(len(tree)):lines.append(f'sum+=compiled_gain_gate_{i}(r);')
 lines.append('return sum>='+float(logit).hex()+';}');Path(a.output).write_text('\n'.join(lines)+'\n');print('gain gate trees',len(tree),'bytes',Path(a.output).stat().st_size);raise SystemExit(0)
root=simplify(tree[0]['tree_structure']);lines=['// Development-trained selective residual gate. true means run the full correction.', 'static bool compiled_needs_correction(Features&r){']
def emit(n):
 if isinstance(n,bool):lines.append('return '+str(n).lower()+';');return
 f,t,left,right=n;lines.append(f'if(r.integer<{f}>()<={t}){{');emit(left);lines.append('}else{');emit(right);lines.append('}')
emit(root);lines.append('}');Path(a.output).write_text('\n'.join(lines)+'\n');print('gate branches',sum('if(' in l for l in lines),'bytes',Path(a.output).stat().st_size)
