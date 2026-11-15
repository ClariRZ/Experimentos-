"""Descomposición agregada de cambios de selección; no exporta identificadores."""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent-prep',type=Path,required=True);p.add_argument('--b6-only',action='store_true');a=p.parse_args();r=a.root
rows=[];composition=[]
def compare(series,meta,paths):
 ids=meta.numero_de_cliente.to_numpy();y=meta.clase_ternaria.to_numpy();base=None
 for arm,path in paths:
  pred=np.load(path);assert len(pred)==len(ids);selected=np.lexsort((ids,-pred))[:11000]
  counts={c:int((y[selected]==c).sum()) for c in ['BAJA+2','BAJA+1','CONTINUA']};assert sum(counts.values())==11000
  composition.append({'serie':series,'brazo':arm,**counts})
  if base is None:base=selected;continue
  enters=np.setdiff1d(selected,base);exits=np.setdiff1d(base,selected);assert len(enters)==len(exits)
  entered_hits=int((y[enters]=='BAJA+2').sum());lost_hits=int((y[exits]=='BAJA+2').sum())
  rows.append({'serie':series,'brazo':arm,'contactos':11000,'retenidos':int(len(np.intersect1d(selected,base))),'entran':len(enters),'salen':len(exits),'BAJA2_entran':entered_hits,'BAJA2_salen':lost_hits,'delta_BAJA2':entered_hits-lost_hits,'delta_ganancia':1100000*(entered_hits-lost_hits)})
meta=pd.read_parquet(a.parent_prep/'meta_test_sellado.parquet');compare('B6_octubre2019',meta,[(arm,r/'resultados/B6'/arm/'test_scores.npy') for arm in ['B5_CONTROL','B6_FIJO','B6_BO']])
if not a.b6_only:
 meta=pd.read_parquet(r/'preparado/c3_filas.parquet');meta=meta[meta.foto_mes.eq(202106)];compare('C3_junio2021',meta,[(arm,r/'resultados/C3'/arm/'ensemble_scores.npy') for arm in ['C3_CONTROL','C3_HOJA2500','C3_INTRAMES']])
pd.DataFrame(rows).to_csv(r/'cambios_seleccion.csv',index=False);pd.DataFrame(composition).to_csv(r/'composicion_11000.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
