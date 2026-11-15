from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,ensure_ascii=False));t.replace(p)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def curve(ids,labels,scores):
 assert len(ids)==len(labels)==len(scores) and np.isfinite(scores).all()
 order=np.lexsort((np.asarray(ids),-np.asarray(scores)))
 hits=(np.asarray(labels)[order]=='BAJA+2').astype('int64')
 return np.r_[0,np.cumsum(1100000*hits-27500)]
def policy(ids,labels,scores):
 g=curve(ids,labels,scores);k=int(g.argmax());return {'validation_k':k,'fraction':k/len(scores),'validation_gain':int(g[k]),'validation_n':len(scores)}
def transfer(pol,n):return int(n*int(pol['validation_k'])//int(pol['validation_n']))
def formulas(df,manifest):
 vals=[]
 for r in manifest.itertuples():
  a=df[r.fuente_1].to_numpy(dtype='float64',na_value=np.nan);b=df[r.fuente_2].to_numpy(dtype='float64',na_value=np.nan)
  good=np.isfinite(a)&np.isfinite(b);v=np.full(len(df),np.nan)
  with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
   if r.familia=='ticket':np.divide(a,b,out=v,where=good&(b>0))
   elif r.familia=='suma_tarjetas':v[good]=a[good]+b[good]
   else:raise ValueError(r.familia)
   v=v.astype('float32');v[~np.isfinite(v)]=np.nan
  vals.append(v)
 return np.column_stack(vals)
