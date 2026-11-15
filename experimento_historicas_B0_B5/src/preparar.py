"""Construcción por columnas para limitar memoria; sólo historia 2019."""
import argparse,json,gc
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from historicas import labels,period,summaries,ratio,KEYS

p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',required=True);a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
keys=pq.read_table(a.data,columns=KEYS,filters=[('foto_mes','>=',201901),('foto_mes','<=',201912)]).to_pandas()
y=labels(keys)
mask=keys.foto_mes.isin([201903,201904,201905,201906,201908,201910]).to_numpy()
meta=keys.loc[mask].reset_index(drop=True);meta['clase_ternaria']=y[mask]
# El runner de optimización nunca abre etiquetas de octubre.
meta[meta.foto_mes!=201910].to_parquet(out/'meta_desarrollo.parquet',index=False)
meta[meta.foto_mes==201910].to_parquet(out/'meta_test_sellado.parquet',index=False)
meta[KEYS].to_parquet(out/'filas.parquet',index=False)
base=[c for c in pq.ParquetFile(a.data).schema_arrow.names if c not in KEYS+['clase_ternaria']]
cat=[c for c in base if c in ['active_quarter','cliente_vip','internet','tcuentas','tcallcenter','thomebanking','tmobile_app'] or c.endswith(('_status','_delinquency'))]
dates=[c for c in base if any(s in c for s in ['Fvencimiento','Finiciomora','fultimo_cierre','fechaalta'])]
quant=[c for c in base if c not in cat+dates]
families={'original':base,'lags':[c+'_lag'+str(k) for k in [1,2] for c in base], 'deltas':[c+'_delta'+str(k) for k in [1,2] for c in quant], 'medias':[c+'_media3' for c in quant], 'pendientes':[c+'_pendiente3' for c in quant], 'ratios':[c+'_ratio'+str(k) for k in [1,2] for c in quant]}
mat={name:np.lib.format.open_memmap(out/(name+'.npy'),mode='w+',dtype='float32',shape=(len(meta),len(cols))) for name,cols in families.items()}
idx=pd.MultiIndex.from_arrays([keys.numero_de_cliente,period(keys.foto_mes)])
ix=[idx.get_indexer(pd.MultiIndex.from_arrays([keys.numero_de_cliente,period(keys.foto_mes)-k])) for k in [1,2]]
coverage=[];categories={}
train=keys.foto_mes.isin([201903,201904,201905,201906]).to_numpy()
for j,c in enumerate(base):
 s=pq.read_table(a.data,columns=[c],filters=[('foto_mes','>=',201901),('foto_mes','<=',201912)]).to_pandas()[c]
 x=pd.to_numeric(s,errors='coerce').to_numpy(dtype='float64',na_value=np.nan,copy=True)
 if (s.notna().to_numpy() & np.isnan(x)).any():raise ValueError('No numérica '+c)
 x[~np.isfinite(x)]=np.nan
 if c in cat:
  known=np.unique(x[train & np.isfinite(x)])
  categories[c]=known.tolist()
  # Códigos aprendidos sólo de entrenamiento. Desconocidos -> faltante.
  mapped=np.full(len(x),np.nan)
  for code,value in enumerate(known):mapped[x==value]=code
  x=mapped
 lag=[]
 for pos in ix:
  v=np.full(len(x),np.nan);valid=pos>=0;v[valid]=x[pos[valid]];lag.append(v)
 mat['original'][:,j]=x[mask]
 for k in range(2):mat['lags'][:,k*len(base)+j]=lag[k][mask]
 if c in quant:
  q=quant.index(c)
  for k in range(2):
   mat['deltas'][:,k*len(quant)+q]=(x[mask]-lag[k][mask]).astype('float32')
   mat['ratios'][:,k*len(quant)+q]=ratio(x[mask],lag[k][mask])
  avg,slope=summaries(x[mask],lag[0][mask],lag[1][mask])
  mat['medias'][:,q]=avg;mat['pendientes'][:,q]=slope
 for m in [201903,201904,201905,201906,201908]:
  use=(keys.foto_mes.to_numpy()==m)
  coverage.append({'variable':c,'mes':m,'n':int(use.sum()),'missing_original':int(np.isnan(x[use]).sum()),'missing_lag1':int(np.isnan(lag[0][use]).sum()),'missing_lag2':int(np.isnan(lag[1][use]).sum())})
 if j%20==0:print('columnas',j+1,'/',len(base),flush=True)
for v in mat.values():v.flush()
pd.DataFrame(coverage).to_csv(out/'cobertura_desarrollo.csv',index=False)
manifest={'families':families,'categorical':cat+[c+'_lag'+str(k) for k in [1,2] for c in cat],'categorical_mapping_train_only':categories,'quantitative':quant,'dates_only_original_and_lags':dates,'excluded':['numero_de_cliente','foto_mes','clase_ternaria'],'rows':len(meta),'counts':{k:len(v) for k,v in families.items()},'schema_version':1}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('PREPARACION_COMPLETA',manifest['counts'],flush=True)
