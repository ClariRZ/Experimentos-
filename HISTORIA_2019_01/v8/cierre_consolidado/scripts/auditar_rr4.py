"""Real monthly RR4 coverage. Requires exact original dataset; never trains."""
import argparse,hashlib,json,resource,sys
from pathlib import Path
import numpy as np
import polars as pl
from rr4 import rr4,coverage,deduplicate_new
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
base=a.repo/'HISTORIA_2019_01/v7';cfg=json.loads((base/'resultados/agosto/config_frozen.json').read_text())
with a.dataset.open('rb') as f:
 if hashlib.file_digest(f,'sha256').hexdigest()!=cfg['data']['sha256']:raise ValueError('Dataset identity mismatch')
a.output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(base/'scripts'));from fe_core import build_exact_lags
months=[201904,201905,201906,201908,201909,201910];sources=cfg['data']['history_sources']
df=pl.scan_csv(a.dataset,infer_schema_length=20000).filter(pl.col('foto_mes').is_between(201901,201910)).select(['numero_de_cliente','foto_mes',*sources]).collect()
if df.select(['numero_de_cliente','foto_mes']).is_duplicated().any():raise ValueError('Duplicate keys')
if any(df.select(['numero_de_cliente','foto_mes']).null_count().row(0)):raise ValueError('Null keys')
rows=[]
# One source at a time avoids a 129-source four-month wide audit matrix.
for source in sources:
 x=build_exact_lags(df.select(['numero_de_cliente','foto_mes',pl.col(source).cast(pl.Float64),pl.lit(1.).alias('_present')]),[source,'_present'],3).filter(pl.col('foto_mes').is_in(months))
 for month in months:
  sub=x.filter(pl.col('foto_mes')==month)
  raw=sub.select([source,*[f'{source}__lag{k}' for k in range(1,4)]]).to_numpy()
  present=np.isfinite(sub.select(['_present',*[f'_present__lag{k}' for k in range(1,4)]]).to_numpy())
  idx=month//100*12+month%100-1
  historical=[((idx-k)//12)*100+((idx-k)%12+1) for k in range(4)]
  masked=np.broadcast_to([source in cfg['data']['broken_masks'].get(str(m),[]) for m in historical],raw.shape)
  c=coverage(raw,present,masked)
  for j,operation in enumerate(['recency','zero_run','nonzero_run']):
   labels,counts=np.unique(c['category'][:,j],return_counts=True)
   if 'unexpected' in labels:raise ValueError('Unexplained NA')
   rows.append({'source':source,'month':month,'operation':operation,'denominator':'clients','n':len(sub),'exclusive':dict(zip(labels.tolist(),counts.tolist())),'absent_any':int(c['absent_any'].sum()),'original_missing_any':int(c['original_missing_any'].sum()),'mask_any':int(c['mask_any'].sum()),'mask_only_new_na':int(c['mask_only_new_na'][:,j].sum()),'truncated_finite':None if j==0 else int(c['truncated_runs'][:,j-1].sum())})
(a.output/'coverage_rr4.json').write_text(json.dumps(rows,indent=2)+'\n')
(a.output/'resources.json').write_text(json.dumps({'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'note':'RR4 coverage audit only; not training RAM estimate'},indent=2)+'\n')
