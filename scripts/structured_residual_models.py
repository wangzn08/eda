"""Shared discrete TT and multiscale residual prototypes (V99/V101)."""
import numpy as np
import torch
from torch import nn
def modes(x):
 return np.column_stack([x[:,10],x[:,11],x[:,4]%10+10*(x[:,4]<0),x[:,5]%12+12*(x[:,5]<0),np.minimum(x[:,6]//10,11),np.minimum(x[:,7]//12,45)]).astype(np.int64)
class TrainTensor(nn.Module):
 def __init__(self,r):
  super().__init__();dims=[496,496,20,24,12,46];ranks=[1]+[r]*5+[1]
  self.cores=nn.ParameterList([nn.Parameter(torch.randn(n,ranks[i],ranks[i+1])/(ranks[i]**.5)) for i,n in enumerate(dims)])
  self.bias=nn.Parameter(torch.zeros(()));self.scale=nn.Parameter(torch.tensor(.02))
 def forward(self,z):
  v=self.cores[0][z[:,0],0,:]
  for i in range(1,6):v=torch.bmm(v.unsqueeze(1),self.cores[i][z[:,i]]).squeeze(1)
  return self.bias+self.scale*v[:,0]
class MultiScale(nn.Module):
 def __init__(self):
  super().__init__();self.emb=nn.ModuleList([nn.Embedding(65536,4) for _ in range(4)])
  for e in self.emb:nn.init.normal_(e.weight,std=.01)
  self.head=nn.Sequential(nn.Linear(16,32),nn.ReLU(),nn.Linear(32,1))
 def forward(self,z):return self.head(torch.cat([e(z[:,i]) for i,e in enumerate(self.emb)],1))[:,0]
def hashmodes(x):
 # Joint endpoint, signed displacement and spatial boundary codes; not request memoization.
 out=[]
 for level in (1,4,16,64):
  c=np.column_stack([x[:,10],x[:,11],np.floor_divide(x[:,4],level),np.floor_divide(x[:,5],level),np.floor_divide(x[:,0],level),np.floor_divide(x[:,1]%100,level),np.floor_divide(x[:,2],level),np.floor_divide(x[:,3]%100,level)]).astype(np.int64)
  h=np.zeros(len(x),np.int64)
  for j in range(c.shape[1]):h=(h*1000003+c[:,j]*(2*j+17))&0x7fffffff
  out.append(h%65536)
 return np.column_stack(out)
