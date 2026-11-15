"""Synthetic original v7 semantics, no training."""
import sys,unittest
from pathlib import Path
import numpy as np
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'v7/scripts'))
from fe_core import build_exact_lags,sanitize_base,build_window_families
class OriginalTests(unittest.TestCase):
 def frame(self):return pl.DataFrame({'numero_de_cliente':[1]*4,'foto_mes':[201901,201902,201903,201904],'mtest':[1.,2.,3.,4.]})
 def test_lags_calendar(self):
  f=self.frame().filter(pl.col('foto_mes')!=201903);h=build_exact_lags(f,['mtest'],3)
  row=h.filter(pl.col('foto_mes')==201904).row(0,named=True)
  self.assertIsNone(row['mtest__lag1']);self.assertEqual(row['mtest__lag2'],2)
 def test_masks(self):
  f=sanitize_base(self.frame(),['mtest'],{201904:['mtest']});self.assertIsNone(f['mtest'][-1]);self.assertEqual(f['mtest'][2],3)
 def test_t4(self):
  f=build_window_families(build_exact_lags(self.frame(),['mtest'],3),['mtest'],4,include_f1=False,include_f2=True,include_f3=False)
  name=next(n for n in f.columns if '__f2_' in n);self.assertAlmostEqual(f[name][-1],1.)
 def test_r3_requires_complete(self):
  f=self.frame().with_columns(pl.when(pl.col('foto_mes')==201902).then(None).otherwise(pl.col('mtest')).alias('mtest'))
  f=build_window_families(build_exact_lags(f,['mtest'],3),['mtest'],3,include_f1=False,include_f3=True)
  for n in f.columns:
   if '__f3_' in n:self.assertIsNone(f[n][-1])
if __name__=='__main__':unittest.main()
