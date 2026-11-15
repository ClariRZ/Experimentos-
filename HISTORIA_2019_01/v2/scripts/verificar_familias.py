import tempfile,json
from pathlib import Path
import numpy as np
import polars as pl
from continuar_familias import families
from cerrar_v2 import fixed_gain,final_evaluation,select_methods

def test_formulas():
 d=pl.DataFrame({'numero_de_cliente':[1,2,3,4,5],'foto_mes':[201903]*4+[201904],'mx':[3.,0.,-1.,None,9.],'mx__lag1':[2.,0.,1.,1.,9.],'mx__lag2':[1.,0.,2.,1.,9.],'cx':[1.,0.,2.,1.,3.],'cx__lag1':[1.,1.,1.,1.,1.],'cx__lag2':[1.,1.,1.,1.,1.]})
 catalog=[{'feature':'ticket','sources':['mx','cx'],'kind':'C3_TICKETS'},{'feature':'sum','sources':['mx','cx'],'kind':'C3_SUMAS'}]
 z,f=families(d,['mx','cx'],catalog)
 assert z['v2_M1__mx'][0]==2 and z['v2_M2__mx'][0]==1 and z['v2_M3__mx'][0]==3
 assert abs(z['v2_M4__mx'][0]-np.sqrt(2/3))<1e-6
 assert z['v2_T1__mx'][0]==1 and z['v2_Z__mx'][1]==3
 assert z['v2_R__mx'][0]==1.5 and z['v2_R__mx'][1] is None and z['v2_R__mx'][2] is None
 assert z['v2_M1__mx'][3] is None and z['v2_Z__mx'][3] is None
 assert z['v2_K__mx'][4]==1 and z['v2_K__mx'][1]==0 and z['v2_K__mx'][3] is None
 assert z['v2_ticket'][1] is None and z['v2_sum'][3] is None

def test_final_gate():
 with tempfile.TemporaryDirectory() as t:
  p=Path(t);final_evaluation(None,None,None,{},p,{})
  d=json.loads((p/'estado.json').read_text());assert d['octubre_abierto'] is False
 y=np.array([1,0,0,1]);pred=np.array([.8,.8,.2,.1]);ids=np.array([2,1,3,4])
 assert fixed_gain(y,pred,ids,0)==0
 assert fixed_gain(y,pred,ids,.25)==-27500 # score empatado, ID ascendente
 assert fixed_gain(y,pred,ids,.5)==1045000

def test_canaries_keep_raw():
 class Budget:
  def check(self):pass
 with tempfile.TemporaryDirectory() as t:
  rng=np.random.default_rng(7);n=60;x=rng.normal(size=n)
  frame=pl.DataFrame({'numero_de_cliente':np.arange(n),'foto_mes':[201903]*n,'clase_ternaria':['BAJA+2' if v>0 else 'CONTINUA' for v in x],'raw':x,'derived':x*2})
  d=select_methods(frame,['raw'],['raw','derived'],{'seeds':[101,211],'threads':1},Path(t),Budget())
  assert d['gain_columns'][0]=='raw' and d['canary_columns'][0]=='raw' and d['n_canaries']==40 and not d['august_used']

if __name__=='__main__':
 for f in [test_formulas,test_final_gate,test_canaries_keep_raw]:f();print('PASS',f.__name__,flush=True)
 print('VERIFICACION_CONTINUACION_OK',flush=True)
