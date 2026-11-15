"""Pruebas sintéticas; no lee datos reales ni entrena modelos."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import polars as pl
import auditar_v3 as f
from ejecutar_v3 import policy,bootstrap,verdict,identity_hash
class Features(unittest.TestCase):
 def test_preflight(self):f.tests()
 def test_activity_and_broken(self):
  d=pl.DataFrame({f.ID:[1]*4+[2]*3,f.MONTH:[201901,201902,201903,201904,201901,201902,201903],'x':[3.,2.,1.,0.,0.,None,2.]})
  d=f.add_lags_deltas(d,['x']);d=d.with_columns(f.activity(d,'x'))
  self.assertEqual(d['x__caidas3'].to_list(),[None,None,2.,2.,None,None,None])
  self.assertEqual(d['x__apago1'].to_list(),[None,0.,0.,1.,None,None,None])
 def test_ranks_use_previous_month_population(self):
  d=pl.DataFrame({f.ID:[1,2,1,2],f.MONTH:[201901,201901,201902,201902],'x':[10.,20.,15.,5.]})
  d=d.with_columns(f.signed_rank(d,'x'));d=f.add_lags_deltas(d,['x__rank'])
  self.assertEqual(d['x__rank__delta1'].to_list(),[None,None,.5,-.5])
 def test_available_row_with_null_value(self):
  d=f._ensure_panel(pl.DataFrame({f.ID:[1,1],f.MONTH:[201912,202001],'x':[None,1.]}))
  self.assertEqual(f.avail(d)['registro_lag1_disponible'].to_list(),[0.,1.])
 def test_duplicate_keys_rejected(self):
  with self.assertRaises(ValueError):f._ensure_panel(pl.DataFrame({f.ID:[1,1],f.MONTH:[201901]*2}))
class Metrics(unittest.TestCase):
 def test_full_window_against_brute(self):
  ids=np.array([5,2,8,1,9,3,7]);y=np.array([0,1,1,0,1,0,0]);p=np.array([.5,.5,.4,.6,.4,.2,.1]);w=3
  ordered=np.lexsort((ids,-p));g=np.cumsum(np.where(y[ordered],1072500.,-27500.));sm=np.array([g[i-1:i+2].mean() for i in range(1,len(g)-1)]);j=int(sm.argmax())+1
  r=policy(ids,y,p,w);self.assertEqual(r['gain_smoothed'],sm.max());self.assertEqual(r['n_send'],j+1);self.assertEqual(r['gain_at_n'],g[j])
 def test_window_not_shortened(self):
  with self.assertRaises(ValueError):policy(np.arange(5),np.ones(5),np.zeros(5))
 def test_ties_sort_client_id_and_alignment(self):
  ids=np.arange(9);y=ids%2;p=np.ones(9)
  perm=np.array([8,3,1,4,2,6,0,7,5]);self.assertEqual(policy(ids,y,p,3),policy(ids[perm],y[perm],p[perm],3))
 def test_bootstrap_identical_zero(self):
  ids=np.arange(30);y=(ids%3==0).astype(int);p=np.arange(30)/30
  r=bootstrap(ids,y,p,p,20,123,3);self.assertEqual(r['ci90'],[0.,0.]);self.assertEqual(r['replicas_validas'],20)
 def test_bootstrap_deterministic(self):
  ids=np.arange(30);y=(ids%3==0).astype(int);p=np.arange(30)/30
  self.assertEqual(bootstrap(ids,y,p,1-p,20,123,3),bootstrap(ids,y,p,1-p,20,123,3))
 def test_economic_interest_without_auc(self):
  self.assertEqual(verdict([1,1,1,-1,-1],[-1]*5,[-2,3],1),'INDICIO_ECONOMICO')
  self.assertEqual(verdict([10]*5,[-1]*5,[1,20],1),'APORTA')
  self.assertNotEqual(verdict([10]*5,[-1]*5,[1,20],-1),'APORTA')
 def test_checkpoint_identity_changes(self):
  a={'columns':['a','b'],'labels_hash':'1','seed':1};b={**a,'columns':['b','a']}
  self.assertNotEqual(identity_hash(a),identity_hash(b));self.assertNotEqual(identity_hash(a),identity_hash({**a,'labels_hash':'2'}))
 def test_october_gate_in_config(self):
  import json
  c=json.loads((f.ROOT/'configuraciones/protocolo.json').read_text());self.assertFalse(c['october_authorized']);self.assertFalse(c['reoptimization']);self.assertEqual(c['max_hours'],6)
if __name__=='__main__':unittest.main(verbosity=2)
