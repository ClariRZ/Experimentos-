import sys, time, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import polars as pl
from ejecutar_inicial import trim_columns,prepare,Run
from supervisar import supervise

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

def test_watchdog_stops_and_exports_no_private(tmp_path):
 out=tmp_path/'run';out.mkdir();(out/'private').mkdir();(out/'private/secret.json').write_text('{}')
 r=supervise([sys.executable,'-c','import time;time.sleep(60)'],time.time()+.2,out,min_disk=0)
 assert r['reason']=='TIME_CAP' and r['returncode']!=0
 import tarfile
 with tarfile.open(tmp_path/'run_agregados.tar.gz') as t:assert all('private' not in n for n in t.getnames())

def test_real_lightgbm_fit_and_cap(tmp_path):
 r=Run.__new__(Run);r.cfg={'hyperparameter_search':{'fixed':{'objective':'binary','metric':'auc','num_threads':1}}};r.out=tmp_path;r.deadline=time.time()+60;r.fits=0
 rng=np.random.default_rng(101);x=rng.normal(size=(500,4));r.yt=(x[:,0]>0).astype(int);r.yv=r.yt
 m,p,t=r.fit(x,x,{'num_leaves':7,'min_data_in_leaf':10},101,10,True)
 assert len(p)==500 and m.best_iteration>0
 r.fits=77
 import pytest
 with pytest.raises(RuntimeError,match='Fit cap'):r.fit(x,x,{},101,1)
