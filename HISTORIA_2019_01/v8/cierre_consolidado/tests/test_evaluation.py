import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluar_v8 import contributions,bootstrap,classify
class EvaluationTests(unittest.TestCase):
 def test_ties_id_order(self):
  d,s=contributions(np.array([3,1,2]),np.ones(3),np.array([1,0,1]),2)
  self.assertEqual(s.tolist(),[False,True,True]);self.assertEqual(int(d.sum()),1045000)
 def test_duplicate_keys_block(self):
  with self.assertRaises(ValueError):contributions(np.array([1,1]),np.ones(2),np.ones(2),1)
 def test_missing_scores_block(self):
  with self.assertRaises(ValueError):contributions(np.array([1]),np.array([np.nan]),np.ones(1),1)
 def test_bootstrap_shared_indices(self):
  d=np.array([[1,10],[-2,-20],[4,40]]);actual=bootstrap(d,20,42);rng=np.random.default_rng(42)
  expected=np.array([d[rng.integers(0,3,size=3)].sum(axis=0) for _ in range(20)])
  np.testing.assert_array_equal(actual,expected);np.testing.assert_array_equal(actual[:,1],10*actual[:,0])
 def test_negative_september_prevents_favorable(self):
  o={'ensemble_delta':1,'ci_adjusted':[.1,2],'seed_delta_mean':1,'sensitivity_deltas':[1]*5}
  self.assertEqual(classify(o,{'ensemble_delta':-1,'seed_delta_mean':1}),'PROMETEDOR_INCONCLUSO')
 def test_zero_not_promoted(self):
  self.assertEqual(classify({'ensemble_delta':0},{}),'SIN_MEJORA_OBSERVADA')
 def test_all_conditions(self):
  o={'ensemble_delta':1,'ci_adjusted':[.1,2],'seed_delta_mean':1,'sensitivity_deltas':[1,1,0,0,-1]}
  self.assertEqual(classify(o,{'ensemble_delta':1,'seed_delta_mean':1}),'FAVORABLE_DENTRO_DE_ESTE_ANALISIS')
if __name__=='__main__':unittest.main()
