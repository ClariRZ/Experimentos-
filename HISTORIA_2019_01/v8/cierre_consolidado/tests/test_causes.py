import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from auditar_causas import attribute,required_lags
class CausesTests(unittest.TestCase):
 def test_required(self):
  self.assertEqual(required_lags('x__lag2'),[2]);self.assertEqual(required_lags('x__delta2'),[0,2]);self.assertEqual(required_lags('x__f3_rel_prev_W3'),[0,1,2])
 def test_priority_and_unexpected(self):
  a=np.array([True]*6);zero=np.zeros(6,dtype=bool)
  r=attribute(a,np.array([1,0,0,0,0,0],bool),np.array([1,1,0,0,0,0],bool),np.array([1,1,1,0,0,0],bool),np.array([1,1,1,1,0,0],bool),np.array([1,1,1,1,1,0],bool))
  self.assertEqual(r.tolist(),['absent_client_month','original_missing_or_nonfinite','historical_mask','zero_reference','float32_overflow','unexpected'])
 def test_finite_not_overwritten(self):
  self.assertEqual(attribute(np.array([False]),*[np.array([True])]*5).tolist(),['finite'])
if __name__=='__main__':unittest.main()
