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
   assert set(r['B0_J']['columns'])<=set(r[arm]['columns'])
  assert set(meta['foto_mes'].unique())=={201906,201908}
  for family,windows in [('S',[3,4,6]),('T',[4,6]),('R',[3,4,6])]:
   pairs=[{c.rsplit('_W',1)[0] for c in r[f'{family}{w}']['columns'] if c not in r['B0_J']['columns']} for w in windows]
   assert all(x==pairs[0] for x in pairs)
 assert {a:r['columns'] for a,r in regs[0].items()}=={a:r['columns'] for a,r in regs[1].items()}



def test_training_blocked_before_creating_output(tmp_path):
 import argparse,pytest
 cfg=tmp_path/'blocked.json';cfg.write_text(json.dumps({'training_authorized':False}))
 args=argparse.Namespace(config=cfg,output=tmp_path/'run',dataset=tmp_path/'absent',deadline=time.time()+60)
 with pytest.raises(ValueError,match='no autorizado'):Run(args)
 assert not args.output.exists()


def test_common_pair_exclusion_across_windows():
 from ejecutar_etapa1 import common_pairs
 frames={'S3':pl.DataFrame({'b':[1.,2.,3.],'a3':[1.,2.,3.],'z3':[3.,1.,2.]}),'S6':pl.DataFrame({'b':[1.,2.,3.],'a6':[9.,8.,6.],'z6':[2.,3.,1.]})}
 pairs,reasons=common_pairs(frames,{'S3':{'a':'a3','z':'z3'},'S6':{'a':'a6','z':'z6'}},['b'])
 assert pairs==['z'] and reasons['a'][0]['reason']=='exact_duplicate_of:b'

def test_slope3_identity_and_long_window_missingness():
 from fe_core import build_exact_lags,add_baseline_lags_deltas,build_window_families
 d=pl.DataFrame({'numero_de_cliente':[1]*6,'foto_mes':list(range(201901,201907)),'x':[1.,None,5.,7.,10.,15.]})
 h=add_baseline_lags_deltas(build_exact_lags(d,['x'],5),['x'])
 w=build_window_families(h,['x'],3,include_f2=True)
 row=w.filter(pl.col('foto_mes')==201906).row(0,named=True)
 assert row['x__f2_slope_W3']==row['x__delta2']/2
 w=build_window_families(h,['x'],6,include_f2=True)
 row=w.filter(pl.col('foto_mes')==201906).row(0,named=True)
 assert all(row[c] is None for c in row if '_W6' in c)
