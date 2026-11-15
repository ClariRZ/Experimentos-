import json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ejecutar_v8 import Checkpoints,choose_finalists,choose_confirmed,cutoff,validate_contract
class ExecutorTests(unittest.TestCase):
 def test_draft_cannot_train(self):
  with self.assertRaises(ValueError):validate_contract({'status':'DRAFT','training_authorized':False})
 def test_finalists_tie_earliest(self):
  rows=[{'trial':i,'state':'COMPLETE','auc':a} for i,a in [(3,.8),(1,.8),(2,.9),(0,.7)]]
  self.assertEqual([r['trial'] for r in choose_finalists(rows)],[2,1,3])
 def test_failed_search_blocks(self):
  with self.assertRaises(ValueError):choose_finalists([{'state':'FAIL','auc':.9}])
 def test_confirmation_not_search_auc(self):
  rows=[{'trial':0,'auc':.99,'aucs':[.7,.7],'rounds':30},{'trial':1,'auc':.8,'aucs':[.8,.8],'rounds':40}]
  self.assertEqual(choose_confirmed(rows)['trial'],1)
 def test_confirmation_tie_rules(self):
  rows=[{'trial':0,'aucs':[.5,.5],'rounds':20},{'trial':1,'aucs':[.4,.6],'rounds':5},{'trial':2,'aucs':[.5,.5],'rounds':10},{'trial':3,'aucs':[.5,.5],'rounds':10}]
  self.assertEqual(choose_confirmed(rows)['trial'],2)
 def test_integer_contacts(self):
  self.assertEqual(cutoff(3481,131887,135754),3481*135754//131887)
 def test_resume_does_not_fit(self):
  with tempfile.TemporaryDirectory() as d:
   cp=Checkpoints(d,{'version':1});calls=[]
   def fit(p):calls.append(1);(p/'model.txt').write_text('fake');return {'auc':.8}
   cp.run('B0_final_1',{'seed':1},fit);cp.run('B0_final_1',{'seed':1},fit)
   self.assertEqual(len(calls),1)
 def test_tamper_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   cp=Checkpoints(d,{});cp.run('fit',{},lambda p: (p/'model.txt').write_text('a'))
   (Path(d)/'fit/model.txt').write_text('b')
   with self.assertRaises(ValueError):cp.load('fit',{})
 def test_interruption_blocks_retry(self):
  with tempfile.TemporaryDirectory() as d:
   cp=Checkpoints(d,{})
   def fail(p):raise RuntimeError('power loss')
   with self.assertRaises(RuntimeError):cp.run('fit',{},fail)
   with self.assertRaises(RuntimeError):cp.run('fit',{},lambda p:None)
 def test_identity_change_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   Checkpoints(d,{'code':'a'})
   with self.assertRaises(ValueError):Checkpoints(d,{'code':'b'})
 def test_tpe_replay(self):
  import optuna
  def replay(known):
   s=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=2026111307,n_startup_trials=5))
   params=[]
   for i in range(12):
    t=s.ask();x=t.suggest_float('x',.01,.1,log=True);params.append(x);s.tell(t,known[i] if i<len(known) else -(x-.04)**2)
   return params
  values=replay([]);self.assertEqual(values,replay([-(x-.04)**2 for x in values[:7]]))
if __name__=='__main__':unittest.main()
