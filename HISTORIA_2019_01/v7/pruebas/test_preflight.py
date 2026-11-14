import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from preflight import coverage_provenance,capture_environment
from ejecutar_v7 import history

class PreflightTests(unittest.TestCase):
    def test_missing_causes_and_calendar(self):
        df=pl.DataFrame({'numero_de_cliente':[1,1,1,2,2,2,2],
                         'foto_mes':[201901,201903,201904,201901,201902,201903,201904],
                         'x':[5.,None,0.,float('inf'),4.,6.,0.]})
        cfg={'data':{'history_sources':['x'],'broken_masks':{'201903':['x']}}}
        r=coverage_provenance(df,cfg,[201904])['months']['201904']['sources']['x']
        self.assertEqual(r['slots_current_then_lags']['0']['observed'],2)
        self.assertEqual(r['slots_current_then_lags']['1']['sanitation'],2)
        self.assertEqual(r['slots_current_then_lags']['2']['absent_client_month'],1)
        self.assertEqual(r['slots_current_then_lags']['3']['nonfinite'],1)
        self.assertEqual(r['strict_windows']['4']['incomplete'],2)
        cfg['data']['broken_masks']={}
        r=coverage_provenance(df,cfg,[201904])['months']['201904']['sources']['x']
        self.assertEqual(r['slots_current_then_lags']['1']['original_missing'],1)
    def test_actual_contract_keeps_october_zero_and_null(self):
        cfg=json.loads((Path(__file__).resolve().parents[1]/'configuraciones/contrato_v7.json').read_text())
        self.assertNotIn('201910',cfg['data']['broken_masks'])
        self.assertNotIn('201907',cfg['data']['broken_masks'])
        cfg['data']['history_sources']=['mrentabilidad']
        df=pl.DataFrame({'numero_de_cliente':[1,2],'foto_mes':[201910,201910],'mrentabilidad':[0.,None]})
        h,_=history(df,cfg,[201910])
        self.assertEqual(h['mrentabilidad'].to_list(),[0.,None])
    def test_runtime_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'Runtime packages'):
            capture_environment({'runtime':{'packages':{'numpy':'invalid'}}})
