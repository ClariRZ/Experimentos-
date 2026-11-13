"""Orchestration test using a fake model: no real training."""
import json,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ejecutar_etapa1 import Run,ARMS

def test_all_arms_trials_seeds_and_contrasts_without_training(tmp_path):
 r=Run.__new__(Run)
 r.cfg=json.loads((Path(__file__).resolve().parents[1]/'configuraciones/contrato_v6.json').read_text())
 r.out=tmp_path;r.art=tmp_path/'private';r.art.mkdir();r.fits=0;r.results={};r.start=time.time()
 r.registry={a:{'columns':['x'],'matrix_file_sha256':'synthetic','status':'IDENTIFICABLE'} for a in ARMS}
 r.ids=np.arange(3000);r.yv=(r.ids%13==0).astype(int)
 r.matrices=lambda arm:(np.zeros((10,1)),np.zeros((3000,1)))
 class Fake:
  best_iteration=7
  def save_model(self,path):Path(path).write_text('synthetic test fixture')
 def fit(xt,xv,hp,seed,rounds,early=False):
  r.fits+=1
  return Fake(),np.random.default_rng(seed).random(3000),0.0
 r.fit=fit;r.execute()
 f=json.loads((tmp_path/'FINAL.json').read_text())
 assert f['fits']==165 and f['arms']==ARMS and len(f['comparisons'])==18
 for arm in ARMS:
  assert len(json.loads((tmp_path/arm/'trials.json').read_text()))==10
  assert [s['seed'] for s in json.loads((tmp_path/arm/'seeds.json').read_text())]==[211,307,401,503,601]
 assert f['october_used'] is False
