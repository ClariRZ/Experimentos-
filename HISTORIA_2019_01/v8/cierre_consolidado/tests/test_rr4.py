import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from rr4 import rr4,calendar_window,coverage,deduplicate_new
class Tests(unittest.TestCase):
 def test_examples(self):
  np.testing.assert_equal(rr4([[0,np.nan,50,10],[np.nan,50,0,0],[0,0,0,0],[-5,-2,0,9]]),[[2,1,0],[1,np.nan,np.nan],[np.nan,4,0],[0,0,2]])
 def test_all_missing(self): self.assertTrue(np.isnan(rr4([[np.nan]*4])).all())
 def test_inf(self): np.testing.assert_equal(rr4([[np.inf,2,0,0]]),[[1,np.nan,np.nan]])
 def test_year(self):
  w,p=calendar_window([1,1],[201912,202001],[2,0]);np.testing.assert_equal(rr4(w)[1],[1,1,0])
 def test_gap(self):
  w,p=calendar_window([1,1],[201901,201903],[50,0]);np.testing.assert_equal(rr4(w)[1],[2,1,0]);self.assertFalse(p[1,1])
 def test_duplicate(self):
  with self.assertRaises(ValueError):calendar_window([1,1],[201901,201901],[1,2])
 def test_order_and_future(self):
  w,_=calendar_window([1,1,1],[201903,201901,201904],[0,50,999]);np.testing.assert_equal(rr4(w)[0],[2,1,0])
 def test_mask_provenance(self):
  a=coverage([[0,2,0,0]],[[1]*4],[[0,1,0,0]])
  self.assertEqual(a['category'][0,0],'historical_mask');self.assertTrue(a['truncated_runs'][0,0])
 def test_empty_vs_partial(self):
  a=coverage([[0]*4,[0]*4],[[1]*4,[1,0,1,1]],[[0]*4]*2)
  self.assertEqual(a['category'][0,0],'complete_window_no_nonzero');self.assertEqual(a['category'][1,0],'absent_client')
 def test_trim(self):
  k,e=deduplicate_new({'base':[1,np.nan,1]},{'same':[1,np.nan,1],'const':[2,2,2],'rare':[0,0,1],'missing':[np.nan]*3})
  self.assertEqual(set(k),{'base','rare'});self.assertEqual(e['same'],'duplicate:base')
 def test_shape(self):
  with self.assertRaises(ValueError):rr4([[1,2]])
 def test_semantics_exhaustive_reference(self):
  import itertools
  # Direct equivalent of the audited C3 loop, all 4**4 combinations.
  for vals in itertools.product([0.,-2.,5.,np.nan],repeat=4):
   rec=np.nan;zr=nr=0;zc=nc=np.isfinite(vals[0])
   for k,a in enumerate(vals):
    ao=np.isfinite(a)
    if np.isnan(rec) and ao and a!=0:rec=k
    zc=zc and ao and a==0;nc=nc and ao and a!=0
    zr+=zc;nr+=nc
   np.testing.assert_equal(rr4([vals])[0],[rec,zr if np.isfinite(vals[0]) else np.nan,nr if np.isfinite(vals[0]) else np.nan])
if __name__=='__main__':unittest.main()
