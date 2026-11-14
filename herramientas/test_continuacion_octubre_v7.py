from pathlib import Path
import sys,json,time,hashlib
import numpy as np
import polars as pl
repo=Path(__file__).resolve().parents[1]
root=repo/'HISTORIA_2019_01/v7'
sys.path.insert(0,str(root/'scripts'))
from ejecutar_v7 import Runner
from argparse import Namespace
import tempfile
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);rng=np.random.default_rng(9);n=2001
 ids=np.repeat(np.arange(1,n+1),10);months=np.tile(np.arange(201901,201911),n)
 x=rng.normal(size=len(ids));z=rng.uniform(-2,8,len(ids));r=rng.random(len(ids))
 labels=np.where(r<.08,'BAJA+2',np.where(r<.15,'BAJA+1','CONTINUA'))
 df=pl.DataFrame({'numero_de_cliente':ids,'foto_mes':months,'clase_ternaria':labels,'x':x,'z':z})
 data=p/'synthetic.csv';df.write_csv(data)
 c=json.loads((root/'configuraciones/contrato_v7_propuesto.json').read_text())
 c['data']['sha256']=hashlib.sha256(data.read_bytes()).hexdigest();c['data']['history_sources']=['x','z'];c['data']['broken_masks']={}
 c['real_audit_approved']=True;c['sanitation_review']={'resolved':True,'synthetic_only':True}
 ap=p/'audit.json';ap.write_text('{}');c['real_audit_file']='audit.json';c['real_audit_sha256']=hashlib.sha256(ap.read_bytes()).hexdigest()
 c['hyperparameter_search']['max_rounds']=3;c['hyperparameter_search']['early_stopping_rounds']=2
 c['hyperparameter_search']['range']['num_leaves']={'type':'int','low':3,'high':8}
 c['hyperparameter_search']['range']['min_data_in_leaf']={'type':'int','low':5,'high':20}
 cp=p/'config.json';cp.write_text(json.dumps(c))
 a=Namespace(config=cp,dataset=data,output=p/'result',deadline=time.time()+600)
 run=Runner(a);run.train();run.october()
 import importlib.util
 import ejecutar_v7 as original
 spec=importlib.util.spec_from_file_location('continuation',repo/'herramientas/evaluar_octubre_v7.py')
 continuation=importlib.util.module_from_spec(spec);spec.loader.exec_module(continuation)
 continuation.load_original=lambda source: original
 (a.output/'FINAL.json').rename(a.output/'ORIGINAL_FINAL.saved')
 run.state('DEVELOPMENT_FROZEN')
 def no_fit(*args,**kwargs): raise AssertionError('Continuation tried to train')
 original.Runner.fit=no_fit
 continued=p/'continued'
 continuation.evaluate(a.output,continued,data,time.time()+600,True)
 for arm in original.ARMS:
  old=json.loads((a.output/arm/'result_october.json').read_text())
  new=json.loads((continued/arm/'result_october.json').read_text())
  assert old==new,arm
 assert json.loads((a.output/'comparisons_201910.json').read_text())==json.loads((continued/'comparisons_201910.json').read_text())
 assert len(list(a.output.glob('private/*.parquet')))==1 # metadata only
 assert json.loads((continued/'FINAL.json').read_text())['new_fits']==0
 (a.output/'ORIGINAL_FINAL.saved').rename(a.output/'FINAL.json')
 print('CONTINUATION_PASS: 50 exact August checks; all ten October results and all bootstrap comparisons identical; no fitting.')
 final=json.loads((a.output/'FINAL.json').read_text());assert final['fits']==150
 assert len(json.loads((a.output/'comparisons_201908.json').read_text())['rows'])==11
 report={'synthetic_only':True,'not_actual_experiment':True,'fits':final['fits'],'maximum_rounds_per_fit':3,
 'arms':len(final['arms']),'august_predictions_exact':final['august_predictions_regenerated'],
 'both_months_evaluated':True,'seconds':final['seconds']}

 print('SYNTHETIC_SUCCESS',report)
