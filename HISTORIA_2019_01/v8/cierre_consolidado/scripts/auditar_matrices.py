"""Audit real frozen schemas and derive RR4 schema from train only; never fit."""
import argparse,gc,hashlib,json,resource,sys,time
from pathlib import Path
import numpy as np
import polars as pl
from rr4 import rr4
from diagnostico_octubre import VARS
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
def save(name,x):(a.output/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
b=a.repo/'HISTORIA_2019_01/v7';cfg=json.loads((b/'resultados/agosto/config_frozen.json').read_text());reg=json.loads((b/'resultados/agosto/feature_manifest.json').read_text())
with a.dataset.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==cfg['data']['sha256']
sys.path.insert(0,str(b/'scripts'));import ejecutar_v7 as m
start=time.monotonic();data=m.read_data(a.dataset,list(range(201901,201911)))
assert set(data[m.LABEL].drop_nulls().unique())<= {'CONTINUA','BAJA+1','BAJA+2'}
assert data[m.LABEL].null_count()==0
raw=[c for c in data.columns if c not in [m.ID,m.MONTH,m.LABEL]];assert len(raw)==152
save('poblacion.json',data.group_by(m.MONTH,m.LABEL).len().sort([m.MONTH,m.LABEL]).to_dicts())
statistics=[]
for month in sorted(data[m.MONTH].unique()):
 part=data.filter(pl.col(m.MONTH)==month)
 for c in VARS:
  s=part[c];statistics.append({'month':month,'variable':c,'rows':len(part),'nulls':s.null_count(),'zeros':int((s==0).sum()),'distinct':s.n_unique()})
save('anomalias_sin_tratamiento.json',statistics)
labels=data.select([m.ID,m.MONTH,m.LABEL]);data=data.drop(m.LABEL)
coverage=[];train=[]
for month in [201904,201905,201906,201908,201909,201910]:
 print('AUDIT_MONTH',month,flush=True)
 hist,_=m.history(data.filter(pl.col(m.MONTH).is_between(month-3,month)),cfg,[month])
 base=m.numeric(hist.select(reg['B0']['columns']),reg['B0']['columns'])
 for arm in ['B0','R3','T4']:
  f=hist if arm=='B0' else m.extras(hist,arm,cfg['data']['history_sources'])[0]
  cols=reg[arm]['columns'];assert not set(cols)&{m.ID,m.MONTH,m.LABEL}
  f=m.numeric(f.select(cols),cols)
  counts=f.null_count().row(0)
  coverage.extend({'month':month,'arm':arm,'column':c,'cells':len(f),'nulls':n} for c,n in zip(cols,counts))
  del f;gc.collect()
 if month<=201906:
  new={}
  for c in cfg['data']['history_sources']:
   v=rr4(hist.select([c,*[f'{c}__lag{k}' for k in range(1,4)]]).to_numpy()).astype(np.float32)
   for j,op in enumerate(['recency','zero_run','nonzero_run']):new[f'{c}__rr4_{op}']=pl.Series(v[:,j],nan_to_null=True)
  train.append(base.hstack(pl.DataFrame(new)))
 del hist,base;gc.collect()
 save('coverage_columns.json',coverage)
# Same cast, missingness and priority as eventual model matrix.
f=pl.concat(train);del train;assert len(f)==381596
basecols=reg['B0']['columns'];kept=list(basecols);groups={};excluded={}
for c in basecols:groups.setdefault(int(f[c].hash(seed=2026).sum()),[]).append(c)
for c in sorted(set(f.columns)-set(basecols)):
 s=f[c]
 if s.null_count()==len(s):excluded[c]='all_missing';continue
 if s.n_unique()==1:excluded[c]='constant';continue
 h=int(s.hash(seed=2026).sum());alias=next((k for k in groups.get(h,[]) if s.equals(f[k],check_dtypes=False)),None)
 if alias is not None:excluded[c]='duplicate:'+alias
 else:kept.append(c);groups.setdefault(h,[]).append(c)
save('rr4_schema.json',{'columns':kept,'excluded':excluded,'train_rows':len(f),'dtype':'float32','baseline_preserved':kept[:len(basecols)]==basecols,'selection_months':[201904,201905,201906]})
save('resources.json',{'seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'rr4_train_matrix_bytes':len(f)*len(kept)*4,'fits':0,'note':'Feature audit, not training peak. Coverage_columns reports availability, not full cause attribution.'})
print('COMPLETE',len(kept),flush=True)
