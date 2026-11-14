"""Boundary cases for inherited formulas and calendar alignment."""
import sys
import unittest
from pathlib import Path
import numpy as np
import polars as pl
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fe_core import build_exact_lags, add_baseline_lags_deltas, build_window_families, build_monthly_rankings, evaluate_gain_curve

class Definitions(unittest.TestCase):
    def test_gap_is_not_previous_row(self):
        d = pl.DataFrame({'numero_de_cliente':[1,1], 'foto_mes':[201901,201903], 'x':[10.,30.]})
        h = build_exact_lags(d,['x'],2).sort('foto_mes')
        self.assertIsNone(h['x__lag1'][-1])
        self.assertEqual(h['x__lag2'][-1],10.)

    def test_known_slope_and_strict_missing(self):
        d = pl.DataFrame({'numero_de_cliente':[1]*4, 'foto_mes':[201901,201902,201903,201904], 'x':[2.,4.,6.,8.]})
        h = build_window_families(build_exact_lags(d,['x'],3),['x'],4,include_f2=True).sort('foto_mes')
        self.assertEqual(h['x__f2_slope_W4'][-1],2.)
        self.assertIsNone(h['x__f2_slope_W4'][2])
        self.assertAlmostEqual(h['x__f3_rel_prev_W4'][-1],1/3)

    def test_zero_denominator_stays_null(self):
        d = pl.DataFrame({'numero_de_cliente':[1]*3,'foto_mes':[201901,201902,201903],'x':[2.,0.,3.]})
        h = build_window_families(build_exact_lags(d,['x'],2),['x'],3).sort('foto_mes')
        self.assertIsNone(h['x__f3_rel_prev_W3'][-1])

    def test_rank_ties_and_nulls(self):
        d = pl.DataFrame({'foto_mes':[201901]*4, 'x':[0.,0.,4.,None]})
        h = build_monthly_rankings(d,['x'])
        self.assertEqual(h['x__rk0'].to_list(),[.5,.5,1.,None])

    def test_frozen_cut_and_tie(self):
        r = evaluate_gain_curve(np.array([2,1,3]),np.array([.5,.5,.1]),np.array([0,1,0]),frozen_prop=.5)
        self.assertEqual(r['cut_contacts'],1)
        self.assertEqual(r['point_gain'],1072500.)

if __name__ == '__main__':
    unittest.main()
