"""V102 zero/positive/negative error regimes with independent conditional experts."""
import json,time
import numpy as np
from catboost import CatBoostClassifier,CatBoostRegressor
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_asymmetric_boundary import read,spatial
from experiment_v7_teacher import score

def main():
 start=time.monotonic();out=ROOT/'out/v102';out.mkdir(exist_ok=True)
 x,y,_,_=load('development');v,yv,_,_=load('validation');b=read('development.v93-joint.csv');bv=read('validation.v93-base.csv');a=spatial(x,b);av=spatial(v,bv);e=y-b;mask=y>0
 classes=np.where(e>2,2,np.where(e< -2,0,1))
 c=CatBoostClassifier(iterations=192,depth=8,learning_rate=.1,loss_function='MultiClass',thread_count=2,random_seed=20261007,verbose=64,allow_writing_files=False)
 c.fit(a[mask],classes[mask],sample_weight=1000/np.maximum(y[mask],100));c.save_model(str(out/'gate.cbm'));prob=c.predict_proba(av,thread_count=2)
 corrections=[]
 for cl in (0,2):
  select=mask&(classes==cl);r=CatBoostRegressor(iterations=256,depth=8,learning_rate=.08,loss_function='MAE',thread_count=2,random_seed=20261007,verbose=64,allow_writing_files=False)
  r.fit(a[select],e[select]/100,sample_weight=1000/np.maximum(y[select],100));r.save_model(str(out/f'expert-{cl}.cbm'));corrections.append(r.predict(av,thread_count=2)*100)
 dneg=np.minimum(corrections[0],0);dpos=np.maximum(corrections[1],0);report={'fit_split':'development','holdout_used':False,'scope':'Research gated architecture; no C++ or file-budget claim','candidates':[]}
 for threshold in (.4,.5,.7,.9):
  cl=prob.argmax(1);delta=np.where((cl==0)&(prob[:,0]>=threshold),dneg,np.where((cl==2)&(prob[:,2]>=threshold),dpos,0));p=np.rint(np.maximum(0,bv+delta));np.save(out/f'gate-{threshold}.npy',p);report['candidates'].append({'threshold':threshold,'score':score(yv,p),'corrected_fraction':float(np.mean(delta!=0))})
 p=np.rint(np.maximum(0,bv+prob[:,0]*dneg+prob[:,2]*dpos));report['candidates'].append({'threshold':'soft-expectation','score':score(yv,p)});np.save(out/'soft.npy',p)
 report['elapsed_seconds']=time.monotonic()-start;print(json.dumps(report,indent=2),flush=True);(ROOT/'reports/V102-gated-residual.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
