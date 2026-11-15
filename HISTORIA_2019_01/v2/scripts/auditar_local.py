"""Auditoría sin entrenar ni leer etiquetas; sólo agregados de calidad e historia."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'auditoria'
SRC=Path('/home/clara-m-rodr-guez/Escritorio/competencia_02_crudo.parquet')
keys=pd.read_parquet(SRC,columns=['numero_de_cliente','foto_mes'])
months=keys.foto_mes.unique(); print('Meses',sorted(months),flush=True)
k=keys.loc[keys.foto_mes.between(201901,201910)].copy().reset_index(drop=True)
k['month_index']=(k.foto_mes//100)*12+k.foto_mes%100
idx=pd.MultiIndex.from_frame(k[['numero_de_cliente','month_index']])
assert not idx.has_duplicates
history={h:idx.get_indexer(pd.MultiIndex.from_arrays([k.numero_de_cliente,k.month_index-h])) for h in range(1,7)}
target=[201903,201904,201905,201906,201908,201910]
coverage=[]
for m in target:
 mask=k.foto_mes.eq(m).to_numpy()
 for h,loc in history.items():
  coverage.append(dict(mes=m,familia=f'lag{h}',cobertura_filas=float((loc[mask]>=0).mean())))
 for w in range(3,7):
  ok=np.logical_and.reduce([history[h]>=0 for h in range(1,w)])
  coverage.append(dict(mes=m,familia=f'ventana{w}',cobertura_filas=float(ok[mask].mean())))
pd.DataFrame(coverage).to_csv(OUT/'cobertura_clientes_calendario.csv',index=False)
cols=[x for x in pq.ParquetFile(SRC).schema_arrow.names if x not in ['numero_de_cliente','foto_mes','clase_ternaria']]
quality=[]; hist=[]
for start in range(0,len(cols),12):
 batch=cols[start:start+12]
 d=pd.read_parquet(SRC,columns=['numero_de_cliente','foto_mes']+batch,filters=[('foto_mes','>=',201901),('foto_mes','<=',201910)])
 assert np.array_equal(d[['numero_de_cliente','foto_mes']].to_numpy(),k[['numero_de_cliente','foto_mes']].to_numpy())
 for col in batch:
  s=d[col]; valid=s.notna().to_numpy(); num=pd.to_numeric(s,errors='coerce')
  for m in sorted(d.foto_mes.unique()):
   z=s[d.foto_mes.eq(m)]; nz=num[d.foto_mes.eq(m)]
   quality.append(dict(variable=col,mes=int(m),filas=len(z),validos=int(z.notna().sum()),na_pct=float(z.isna().mean()*100),ceros_pct=float(nz.eq(0).mean()*100),nunique=int(z.nunique()),dominante_pct=float(z.value_counts(normalize=True).iloc[0]*100) if z.notna().any() else None,mediana=float(nz.median()) if nz.notna().any() else None,p01=float(nz.quantile(.01)) if nz.notna().any() else None,p99=float(nz.quantile(.99)) if nz.notna().any() else None))
  obs={h:(loc>=0)&valid[np.maximum(loc,0)] for h,loc in history.items()}
  for m in target:
   mask=k.foto_mes.eq(m).to_numpy()
   for h in history:
    hist.append(dict(variable=col,mes=m,familia=f'lag{h}',cobertura=float(obs[h][mask].mean())))
    hist.append(dict(variable=col,mes=m,familia=f'delta{h}_actual_menos_lag',cobertura=float((valid&obs[h])[mask].mean())))
   for w in range(3,7):
    ok=valid&np.logical_and.reduce([obs[h] for h in range(1,w)])
    hist.append(dict(variable=col,mes=m,familia=f'ventana{w}',cobertura=float(ok[mask].mean())))
 print('Columnas auditadas',min(start+12,len(cols)),len(cols),flush=True)
pd.DataFrame(quality).to_csv(OUT/'calidad_variable_mes.csv',index=False)
pd.DataFrame(hist).to_csv(OUT/'cobertura_variable_mes.csv',index=False)
meta=dict(fuente=str(SRC),primer_mes=int(min(months)),ultimo_mes=int(max(months)),filas_total=len(keys),filas_2019_hasta_octubre=len(k),columnas_auditadas=len(cols),duplicados_cliente_mes_total=int(keys.duplicated().sum()),etiquetas_leidas=False,entrenamientos=0,nota='Cobertura no nula; no certifica semántica, escala ni elegibilidad de variables categóricas. Octubre: sólo calidad y cobertura, sin etiquetas ni métricas de modelos.')
meta['sha256']=hashlib.file_digest(SRC.open('rb'),'sha256').hexdigest()
(OUT/'auditoria_local.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta),flush=True)
