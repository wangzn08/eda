"""Develop a tiny correction over V158 under the new 600 s novel-query budget.

Only development labels are fitted. Validation selects candidates and is not an
unseen score. Raw coordinates come from the existing native request export;
no chosen-route descriptors, phi dictionary, or teacher outputs are needed.
"""
import argparse,csv,json,time
import numpy as np
import lightgbm as lgb
from architecture import ROOT
from native_research_labels import load_labels

def features(x,b):
 sx,sy,tx,ty=x[:,5],x[:,6],x[:,3],x[:,4]
 dx,dy=tx-sx,ty-sy
 names=['base','sx','sy','tx','ty','sp','tp','dx','dy','ax','ay','qx','qy','rx','ry','sxmod10','symod12','txmod10','tymod12','symod100','tymod100','syband','tyband','sedge_x','tedge_x','sedge_y','tedge_y','cross','samewallband','sourcewall','targetwall','geometric_residual','signed_dx_phase','signed_dy_phase']
 cross=(np.minimum(sx,tx)<76)&(np.maximum(sx,tx)>89)
 columns=[b,sx,sy,tx,ty,x[:,7],x[:,8],dx,dy,abs(dx),abs(dy),abs(dx)//10,abs(dy)//12,abs(dx)%10,abs(dy)%12,sx%10,sy%12,tx%10,ty%12,sy%100,ty%100,sy//100,ty//100,np.minimum(sx,119-sx),np.minimum(tx,119-tx),np.minimum(sy,549-sy),np.minimum(ty,549-ty),cross,sy//100==ty//100,np.minimum(abs(sx-75),abs(sx-90)),np.minimum(abs(tx-75),abs(tx-90)),12*b-150*abs(dx)-125*abs(dy),(dx%10+10)%10,(dy%12+12)%12]
 return np.column_stack(columns).astype(np.float32),names

def main():
 p=argparse.ArgumentParser();p.add_argument('--version',default='276');p.add_argument('--predictions',default='out/v275/v158-all.csv');a=p.parse_args()
 folder=ROOT/f'out/v{a.version}';folder.mkdir(exist_ok=True)
 labels=load_labels();y,yv=labels['y'],labels['yv'];n=len(y)
 with (ROOT/a.predictions).open() as f:b=np.array([int(r['delay']) for r in csv.DictReader(f)],dtype=np.float64)
 assert len(b)==len(y)+len(yv)
 x=np.memmap(ROOT/'out/v243/all.features.f32',dtype='<f4',mode='r',shape=(len(b),137))
 f,names=features(x,b);np.save(folder/'features.npy',f);np.save(folder/'base.npy',b);(folder/'features.json').write_text(json.dumps(names,indent=2)+'\n')
 def score(p):return float(100*np.mean(1-np.tanh(4*abs(p-yv)/np.maximum(yv,1))))
 report={'state':'running','fit_scope':'development labels only','holdout_used':False,'features':len(names),'base_score':score(b[n:]),'candidates':[]}
 for name,leaves,trees,rate in [('one511',511,1,1),('one2047',2047,1,1),('one8191',8191,1,1),('two1023',1023,2,.6),('four511',511,4,.4),('eight255',255,8,.3),('sixteen255',255,16,.2)]:
  start=time.monotonic();path=folder/f'{name}.txt'
  m=lgb.Booster(model_file=str(path)) if path.exists() else lgb.train({'objective':'regression_l1','num_leaves':leaves,'max_depth':24,'min_data_in_leaf':30,'learning_rate':rate,'num_threads':1,'verbosity':-1,'force_col_wise':True,'deterministic':True,'seed':20261019},lgb.Dataset(f[:n],label=y-b[:n],weight=1000/np.maximum(y,1)),num_boost_round=trees)
  m.save_model(str(path));pred=np.rint(np.maximum(0,b[n:]+m.predict(f[n:],num_threads=1)));np.save(folder/f'{name}.npy',pred)
  item={'name':name,'leaves':leaves,'trees':trees,'score':score(pred),'elapsed_seconds':time.monotonic()-start};report['candidates'].append(item);print(json.dumps(item),flush=True);(ROOT/f'reports/V{a.version}-tiny-residual.json').write_text(json.dumps(report,indent=2)+'\n')
 report['state']='complete';(ROOT/f'reports/V{a.version}-tiny-residual.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
