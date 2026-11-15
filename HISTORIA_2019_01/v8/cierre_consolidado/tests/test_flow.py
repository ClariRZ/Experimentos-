"""Exercise the actual training orchestrator with synthetic data and a fake booster."""
import json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ejecutar_v8 as runner

class FlowTests(unittest.TestCase):
 def test_144_planned_stages_and_no_fit_on_resume(self):
  import lightgbm as lgb,optuna
  optuna.logging.set_verbosity(optuna.logging.WARNING)
  base=Path(__file__).resolve().parents[1];repo=base.parents[2]
  c=json.loads((base/'contrato_v8_consolidado.json').read_text())
  c.update(status='APPROVED',training_authorized=True,preflight_passed=True,unresolved=[])
  c['budget'].update(approved=True,required_free_disk_bytes=1,max_rss_bytes=2**50)
  c['history_sources']=['x']
  for arm in runner.ARMS:c['arms'][arm]['columns']=['x']
  c['arms']['RR4']['columns']=['x','x__rr4_zero_run']
  rows=[(i,m,'BAJA+2' if i%2 else 'CONTINUA',float(i%5)) for i in range(20) for m in [201904,201905,201906,201908]]
  data=pl.DataFrame(rows,schema=['numero_de_cliente','foto_mes','clase_ternaria','x'],orient='row')
  def history(frame,cfg,months):
   return frame.with_columns([pl.col('x').alias('x__lag'+str(k)) for k in [1,2,3]]),{}
  old=types.SimpleNamespace(ID='numero_de_cliente',MONTH='foto_mes',LABEL='clase_ternaria',read_data=lambda *a:data,history=history,extras=lambda h,*a:(h,{}),numeric=lambda f,c:f, evaluate_gain_curve=lambda *a:{'cut_contacts':5},payoff=lambda *a:({'gain':0},None))
  calls=[]
  class Booster:
   best_iteration=3
   def predict(self,x,**kw):return np.linspace(.1,.9,len(x))
   def save_model(self,p):Path(p).write_text('SYNTHETIC FAKE BOOSTER - NOT A MODEL')
  def train(*a,**kw):calls.append(1);return Booster()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);dataset=root/'synthetic';dataset.write_text('synthetic only');c['dataset_sha256']=runner.sha(dataset)
   evidence=base/'README.md';c['preflight_evidence']={str(evidence.relative_to(repo)):runner.sha(evidence)}
   config=root/'contract.json';config.write_text(json.dumps(c));out=root/'run'
   argv=['ejecutar_v8','--repo',str(repo),'--config',str(config),'--dataset',str(dataset),'--output',str(out)]
   with patch.object(sys,'argv',argv),patch.dict(sys.modules,{'ejecutar_v7':old}),patch.object(lgb,'train',train):
    runner.main()
    frozen=json.loads((out/'policy_frozen.json').read_text())
    self.assertEqual(len(calls),144);self.assertEqual(frozen['completed_fits'],144)
    self.assertEqual(list(frozen['models']),runner.ARMS)
    self.assertTrue(all(len(m)==10 for m in frozen['models'].values()))
    runner.main()
    self.assertEqual(len(calls),144)
    self.assertEqual(json.loads((out/'status.json').read_text())['status'],'DEVELOPMENT_FROZEN')
if __name__=='__main__':unittest.main()
