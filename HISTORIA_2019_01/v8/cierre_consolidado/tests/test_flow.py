"""Exercise the actual training orchestrator with synthetic data and a fake booster."""
import json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ejecutar_v8 as runner
import evaluar_v8 as evaluator
from operacion_v8 import package,assemble
from diagnostico_octubre import VARS

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
  rows=[(i,m,'BAJA+2' if i%2 else 'CONTINUA',float(i%5)) for i in range(20) for m in [201904,201905,201906,201908,201909,201910]]
  data=pl.DataFrame(rows,schema=['numero_de_cliente','foto_mes','clase_ternaria','x'],orient='row').with_columns([pl.lit(1.).alias(v) for v in VARS])
  def history(frame,cfg,months):
   return frame.filter(pl.col('foto_mes').is_in(months)).with_columns([pl.col('x').alias('x__lag'+str(k)) for k in [1,2,3]]),{}
  old=types.SimpleNamespace(ID='numero_de_cliente',MONTH='foto_mes',LABEL='clase_ternaria',read_data=lambda path,months:data.filter(pl.col('foto_mes').is_in(months)),history=history,extras=lambda h,*a:(h,{}),numeric=lambda f,c:f, evaluate_gain_curve=lambda *a:{'cut_contacts':5},payoff=lambda *a:({'gain':0},None))
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
   eval_args=['evaluar_v8','--repo',str(repo),'--run',str(out),'--dataset',str(dataset)]
   with patch.object(sys,'argv',eval_args),patch.dict(sys.modules,{'ejecutar_v7':old}),patch.object(lgb,'Booster',lambda **kw:Booster()),patch.object(lgb,'train',side_effect=AssertionError('Evaluation must never train')):
    evaluator.main()
    final=json.loads((out/'FINAL.json').read_text())
    self.assertTrue(final['economic_evaluation_complete'])
    self.assertFalse(final['backup_verified'])
    hashes={str(p.relative_to(out)):runner.sha(p) for p in (out/'private/evaluation').glob('*.npz')}
    self.assertEqual(len(hashes),8)
    for month in [201909,201910]:
     report=json.loads((out/f'evaluation_{month}.json').read_text())
     self.assertEqual({report[arm]['K'] for arm in runner.ARMS},{5})
     self.assertTrue(all(report[arm]['ensemble_delta']==0 for arm in runner.ARMS[1:]))
    evaluator.main()
    self.assertEqual(hashes,{name:runner.sha(out/name) for name in hashes})
    model=next((out/'private/checkpoints').glob('B0_final_*/model.txt'));model.write_text('corruption')
    with self.assertRaises(ValueError):evaluator.main()
    model.write_text('SYNTHETIC FAKE BOOSTER - NOT A MODEL')
   manifest=package(out,root/'backup')
   assemble(root/'backup',manifest)
   self.assertTrue(json.loads((root/'backup/RESTORED.json').read_text())['verified'])
   self.assertEqual(len(calls),144)
if __name__=='__main__':unittest.main()
