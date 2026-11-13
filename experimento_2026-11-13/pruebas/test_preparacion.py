import sys, time, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import polars as pl
from entrenar_desde_cero import trim_columns,prepare,Run

def test_selection_keeps_missingness_and_base_priority():
 d=pl.DataFrame({'raw':[1.,2.,None], 'alias':[1.,2.,None], 'missing':[None]*3,'constant':[2.]*3,'indicator':[0.,None,0.]})
 k,e=trim_columns(d,d.columns,['raw'])
 assert k==['raw','indicator'];assert e['alias']=='exact_duplicate_of:raw'

def test_train_only_and_alignment(tmp_path):
 rows=[{'numero_de_cliente':i,'foto_mes':m,'clase_ternaria':['CONTINUA','BAJA+1','BAJA+2'][i%3],'x':float((i+1)**2+(m%100)**2),'tmobile_app':None,'cmobile_app_trx':None} for m in range(201901,201909) for i in range(8)]
 cfg={'data':{'broken_masks':{},'history_sources':['x']}}
 regs=[]
 for version in range(2):
  d=pl.DataFrame(rows).with_columns(pl.col('tmobile_app').cast(pl.Float64),pl.col('cmobile_app_trx').cast(pl.Float64))
  if version:d=d.with_columns(pl.when(pl.col('foto_mes')==201908).then(-1000.).otherwise(pl.col('x')).alias('x'))
  out=tmp_path/str(version);out.mkdir();art=out/'private';art.mkdir();r=prepare(d,cfg,art,out,lambda:None);regs.append(r)
  meta=pl.read_parquet(art/'meta.parquet')
  for arm in r:
   matrix=pl.read_parquet(art/f'{arm}.parquet');assert matrix.select(['numero_de_cliente','foto_mes']).equals(meta.select(['numero_de_cliente','foto_mes']))
   assert set(r['B0']['columns'])<=set(r[arm]['columns'])
 assert {a:r['columns'] for a,r in regs[0].items()}=={a:r['columns'] for a,r in regs[1].items()}

