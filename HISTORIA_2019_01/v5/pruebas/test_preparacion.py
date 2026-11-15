import sys, time, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import polars as pl
from ejecutar_etapa1 import trim_columns,prepare,Run

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
   assert set(r['B0']['columns'])<=set(r[arm]['columns']) if arm!='L' else r[arm]['columns']==[c for c in r['B0']['columns'] if not c.endswith(('__delta1','__delta2'))]
 assert {a:r['columns'] for a,r in regs[0].items()}=={a:r['columns'] for a,r in regs[1].items()}



def test_family_separation_and_v4_baseline_parity(tmp_path):
 import importlib.util
 original=Path(__file__).resolve().parents[3]/'experimento_2026-11-13/scripts/entrenar_desde_cero.py'
 if not original.exists():
  import pytest
  pytest.skip('Referencia v4 local no disponible')
 spec=importlib.util.spec_from_file_location('v4_reference',original);v4=importlib.util.module_from_spec(spec);spec.loader.exec_module(v4)
 rng=np.random.default_rng(42)
 rows=[{'numero_de_cliente':i,'foto_mes':m,'clase_ternaria':['CONTINUA','BAJA+1','BAJA+2'][i%3],'x':float(rng.normal()),'tmobile_app':None,'cmobile_app_trx':None} for m in range(201901,201909) for i in range(8)]
 d=pl.DataFrame(rows).with_columns(pl.col('tmobile_app').cast(pl.Float64),pl.col('cmobile_app_trx').cast(pl.Float64))
 cfg={'data':{'broken_masks':{},'history_sources':['x']}}
 for label,fn in [('v4',v4.prepare),('v5',prepare)]:
  out=tmp_path/label;out.mkdir();art=out/'private';art.mkdir();reg=fn(d,cfg,art,out,lambda:None)
 for arm in ['B0','F1']:
  assert pl.read_parquet(tmp_path/'v4/private'/f'{arm}.parquet').equals(pl.read_parquet(tmp_path/'v5/private'/f'{arm}.parquet'))
 for arm,kind in [('P','mean'),('MIN','min'),('MAX','max'),('RANGO','range')]:
  extra=set(reg[arm]['columns'])-set(reg['B0']['columns'])
  assert extra and all(c.endswith(f'__f1_{kind}_W3') for c in extra)

def test_training_blocked_before_creating_output(tmp_path):
 import argparse,pytest
 cfg=Path(__file__).resolve().parents[1]/'configuraciones/etapa1_propuesta.json'
 args=argparse.Namespace(config=cfg,output=tmp_path/'run',dataset=tmp_path/'absent',deadline=time.time()+60)
 with pytest.raises(ValueError,match='no autorizado'):Run(args)
 assert not args.output.exists()
