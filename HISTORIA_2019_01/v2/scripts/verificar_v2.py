from pathlib import Path
import sys,tempfile,json
import numpy as np
import polars as pl
sys.path.insert(0,str(Path(__file__).parent))
from ejecutar_v2 import policy,bootstrap_pair,compare,Experiment
from historia_features import add_lags_deltas,load_and_audit

def test_calendar():
 d=pl.DataFrame({'numero_de_cliente':[1,1,1,2,2],'foto_mes':[201901,201903,201904,201902,201903],'x':[10.,30.,40.,2.,None]})
 z=add_lags_deltas(d,['x'])
 assert z['x__lag1'][1] is None and z['x__lag2'][1]==10 and z['x__delta2'][1]==20
 assert z['x__lag1'][2]==30 and z['x__lag2'][2] is None
 assert z['x__delta1'][4] is None

def test_gain():
 ids=np.arange(9);y=np.array([1,0,1,0,0,0,1,0,0]);p=np.arange(9,0,-1)/10
 d=policy(ids,y,p,3);g=np.cumsum(np.where(y==1,1072500,-27500));sm=np.array([g[i:i+3].mean() for i in range(7)])
 assert d['gain_smoothed']==sm.max() and d['n_send']==int(sm.argmax())+2
 n=2100;ids=np.arange(n);y=(ids%7==0).astype(int);p=np.random.default_rng(1).random(n)
 boot=bootstrap_pair(ids,y,p,p,10,91)
 assert boot['delta_gain_ci90']==[0.,0.] and boot['delta_auc_ci90']==[0.,0.]

def test_load():
 with tempfile.TemporaryDirectory() as t:
  p=Path(t)/'datos.parquet';rows=[]
  for m in range(1,11):
   for i in range(4):rows.append({'numero_de_cliente':i,'foto_mes':201900+m,'clase_ternaria':'NO_LEER_OCTUBRE' if m==10 else ['CONTINUA','BAJA+1','BAJA+2','CONTINUA'][i],'x':float(i)})
  pl.DataFrame(rows).write_parquet(p)
  z,raw,a=load_and_audit({'data':str(p),'expected_raw_features':1,'broken_variables':{'x':[201904]}})
  assert z.filter(pl.col('foto_mes')==201910)['clase_ternaria'].null_count()==4
  assert z.filter(pl.col('foto_mes')==201904)['x'].null_count()==4
  assert a['partitions']=={'train':16,'validation':4,'test':4}

def test_fit_checkpoint():
 with tempfile.TemporaryDirectory() as t:
  n=2103;rows=[]
  for m in [201903,201904,201905,201906,201908]:
   for i in range(n if m==201908 else 20):rows.append({'numero_de_cliente':i,'foto_mes':m,'clase_ternaria':'BAJA+2' if i%5==0 else 'CONTINUA','x':float(i%11)})
  frame=pl.DataFrame(rows);cfg={'seeds':[101,211],'threads':1};e=Experiment(frame,['x'],cfg,Path(t),'synthetic')
  hp={'params':{'num_leaves':3,'learning_rate':.1,'min_data_in_leaf':5,'feature_fraction':.8,'bagging_fraction':.8},'rounds':2}
  a=e.fit('smoke',['x'],hp,2);b=e.fit('smoke',['x'],hp,2);assert np.array_equal(a,b)
  result=compare(Path(t),'same','same',e.ids,e.yv,a,b,10);assert result['verdict']=='NO APORTA'
  try:e.fit('smoke',['x'],{**hp,'rounds':3},2)
  except AssertionError:pass
  else:raise AssertionError('No bloqueó receta cambiada')

if __name__=='__main__':
 for f in [test_calendar,test_gain,test_load,test_fit_checkpoint]:f();print('PASS',f.__name__,flush=True)
 print('VERIFICACION_V2_OK',flush=True)
