import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import polars as pl
from ejecutar_etapa1 import prepare
from evaluar_octubre import build_history,arm_frame
from fe_core import evaluate_gain_curve
import numpy as np

def test_inference_preserves_august_frozen_features(tmp_path):
 rows=[{'numero_de_cliente':i,'foto_mes':m,'clase_ternaria':['CONTINUA','BAJA+1','BAJA+2'][i%3],'x':float((i+1)**2+(m%100)**2),'tmobile_app':None,'cmobile_app_trx':None} for m in range(201901,201911) for i in range(8) if not (i==2 and m==201905)]
 d=pl.DataFrame(rows).with_columns(pl.col('tmobile_app').cast(pl.Float64),pl.col('cmobile_app_trx').cast(pl.Float64))
 cfg={'data':{'broken_masks':{'201904':['x']},'history_sources':['x']}}
 art=tmp_path/'private';art.mkdir();reg=prepare(d.filter(pl.col('foto_mes')<=201908),cfg,art,tmp_path,lambda:None)
 hist=build_history(d.drop('clase_ternaria'),cfg)
 for arm,r in reg.items():
  got=arm_frame(hist,arm,r['columns'],['x']).filter(pl.col('foto_mes')==201908)
  expected=pl.read_parquet(art/f'{arm}.parquet').filter(pl.col('foto_mes')==201908)
  assert got.equals(expected)

def test_frozen_cut_no_october_optimization():
 r=evaluate_gain_curve(np.array([2,1,3]),np.array([.5,.5,.1]),np.array([1,0,1]),frozen_prop=.5)
 assert r['cut_contacts']==1 and r['point_gain']==-27500
