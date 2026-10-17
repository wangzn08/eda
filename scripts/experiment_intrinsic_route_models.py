"""Use estimator coefficients as quality indicators; development-only residual fit."""
import json,time,numpy as np,lightgbm as lgb
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_asymmetric_boundary import spatial
from experiment_v7_teacher import score
out=ROOT/'out/v125';x,y,_,_=load('development');v,yv,_,_=load('validation');p=np.loadtxt(out/'all.prediction.csv',delimiter=',',skiprows=1,usecols=2,dtype=np.int64);t=np.loadtxt(out/'all.descriptors.csv',delimiter=',',skiprows=1,dtype=np.float32);assert len(p)==850758 and t.shape==(850758,22);n=len(y);b,bv=p[:n],p[n:];r,rv=t[:n],t[n:];prior=np.load(ROOT/'out/v117/route-data.npz');assert np.array_equal(b,prior['development_base']) and np.array_equal(bv,prior['validation_base']);start=time.monotonic()
def features(z,base,r):
 # No golden label participates in the feature builder.
 basefields=spatial(z,base);curvature=r[:,17]-r[:,16]-4*(r[:,16]-r[:,15]);extras=np.column_stack((r,curvature,r[:,18]-r[:,17],r[:,15]-12.5*np.abs(r[:,6])-125/12*np.abs(r[:,7]),r[:,19]*np.maximum(0,r[:,4]-1),r[:,20]*np.minimum(r[:,4]/5,r[:,5]/6),r[:,0]//8,r[:,1]//8,(r[:,0]-r[:,1])%8,r[:,12]==0,r[:,15]==r[:,18],r[:,2]%10,r[:,3]%12));return np.column_stack((basefields,extras)).astype(np.float32)
a,av=features(x,b,r),features(v,bv,rv);np.savez(out/'fit-features.npz',a=a,av=av,y=y,yv=yv,b=b,bv=bv)
report={'state':'running','fit_split':'development','holdout_used':False,'descriptor_predictions_match_v116':True,'scope':'Python prototype; C++/size/throughput pending','candidates':[]}
for name,leaves,trees in [('single',2047,1),('small',127,32),('large',511,256)]:
 ds=lgb.Dataset(a,label=y-b,weight=1000/np.maximum(y,1));m=lgb.train({'objective':'regression_l1','learning_rate':1 if trees==1 else .07,'num_leaves':leaves,'min_data_in_leaf':30,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261007},ds,num_boost_round=trees);m.save_model(str(out/f'{name}.txt'))
 for prefix in sorted(set([trees]+([32,64,128] if trees>=256 else []))):
  q=np.rint(np.maximum(0,bv+m.predict(av,num_iteration=prefix,num_threads=1)));np.save(out/f'{name}-{prefix}.npy',q);item={'name':name,'trees':prefix,'score':score(yv,q),'elapsed':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True)
 (ROOT/'reports/V125-intrinsic-route-models.json').write_text(json.dumps(report,indent=2)+'\n')
report['state']='complete';(ROOT/'reports/V125-intrinsic-route-models.json').write_text(json.dumps(report,indent=2)+'\n')
